import secrets
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import select, inspect, update
from sqlalchemy.orm import sessionmaker
from app.core.config import ROOT, settings
from app.core.security import verify_password, token_hash, utcnow
from app.db.models import Base, User, SessionToken, Instrument, Watch, Event, Strategy, Job, Account, Proposal, Audit, Annotation, Notification
from app.db.session import engine
from app.db.seed import seed
from app.domain.contracts import Login, StrategySpec, BacktestRequest, ResearchRequest, ProposalRequest, ApprovalRequest, KillRequest, AnnotationRequest
from app.marketdata.demo import visible_bars, DATASET_VERSION
from app.quant.indicators import compute
from app.jobs.runner import LocalJobRunner
from app.execution.service import create_proposal, approve
from app.domain import responses as dto
from app.core.errors import ApiError, error_response, install_handlers
from app.jobs.snapshots import freeze_input, verified_snapshot


def record(obj):
    return {c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs}


def create_app(db_engine=None):
    db_engine = db_engine or engine
    sessions = sessionmaker(db_engine, expire_on_commit=False)
    @asynccontextmanager
    async def lifespan(app):
        settings.validate_mode()
        if not inspect(db_engine).has_table("users"):
            raise RuntimeError("Database not initialized. Run scripts/migrate.py first.")
        with sessions() as db:
            seed(db)
        app.state.runner = LocalJobRunner(sessions)
        app.state.runner.recover()
        yield
        app.state.runner.close()

    app = FastAPI(title="AiTrader", version="0.2.0", lifespan=lifespan,
                  responses={code: {"model": dto.ErrorResponse} for code in [400, 401, 403, 404, 405, 409, 422, 429, 500, 503]})
    install_handlers(app)
    app.state.sessions = sessions
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "testserver", "api"])

    @app.middleware("http")
    async def security_headers(request, call_next):
        request.state.request_id = uuid.uuid4().hex
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            origin = request.headers.get("origin")
            # Allow this exact loopback server origin (including an isolated test
            # port) and the explicit local Vite proxy. No wildcard external hosts.
            own_origin = f"{request.url.scheme}://{request.url.netloc}"
            loopback_host = request.url.hostname in {"localhost", "127.0.0.1"}
            allowed = {"http://127.0.0.1:5173", "http://localhost:5173"}
            if loopback_host:
                allowed.add(own_origin)
            if origin and origin not in allowed:
                return error_response(request, 403, "ORIGIN_NOT_ALLOWED", "Origin not allowed")
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    def db_session():
        with sessions() as db:
            yield db

    def identity(request: Request, db=Depends(db_session)):
        sid = request.cookies.get("aitrader_session", "")
        session = db.get(SessionToken, token_hash(sid)) if sid else None
        if not session or datetime.fromisoformat(session.expires_at) < utcnow():
            raise HTTPException(401, "Sign in to continue")
        if request.method not in {"GET", "HEAD"} and not secrets.compare_digest(request.headers.get("X-CSRF-Token", ""), session.csrf):
            raise HTTPException(403, "Missing or invalid CSRF token")
        return session

    prefix = "/api/v1"

    @app.get(prefix + "/health", response_model=dto.Health)
    def health():
        return {"status": "ok", "mode": "DEMO", "instance_id": settings.runtime_instance_id}

    @app.post(prefix + "/auth/login", response_model=dto.UserView)
    def login(payload: Login, response: Response, db=Depends(db_session)):
        user = db.get(User, payload.username)
        if not user or not verify_password(payload.password, user.password):
            raise HTTPException(401, "Invalid username or password")
        raw, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(24)
        db.add(SessionToken(id=token_hash(raw), user_id=user.id, csrf=csrf, expires_at=(utcnow() + timedelta(hours=8)).isoformat()))
        db.add(Audit(actor_id=user.id, action="SIGNED_IN", object_id=user.id, detail={}))
        db.commit()
        response.set_cookie("aitrader_session", raw, httponly=True, samesite="strict", secure=False, max_age=28800, path="/")
        return {"id": user.id, "name": user.name, "csrf": csrf}

    @app.get(prefix + "/auth/me", response_model=dto.UserView)
    def me(auth=Depends(identity), db=Depends(db_session)):
        user = db.get(User, auth.user_id)
        return {"id": user.id, "name": user.name, "csrf": auth.csrf}

    @app.post(prefix + "/auth/logout", response_model=dto.Ok)
    def logout(response: Response, auth=Depends(identity), db=Depends(db_session)):
        db.delete(auth)
        db.commit()
        response.delete_cookie("aitrader_session")
        return {"ok": True}

    @app.get(prefix + "/instruments", response_model=list[dto.InstrumentView])
    def instruments(auth=Depends(identity), db=Depends(db_session)):
        watched = set(db.scalars(select(Watch.instrument_id).where(Watch.user_id == auth.user_id)))
        result = []
        for inst in db.scalars(select(Instrument)):
            bar, prior = inst.bars[-1], inst.bars[-2]
            result.append({"id": inst.id, "symbol": inst.symbol, "name": inst.name, "sector": inst.sector, "currency": inst.currency, "color": inst.color, "price": str(bar["close"]), "change_pct": (bar["close"] / prior["close"] - 1) * 100, "as_of": bar["time"], "source": DATASET_VERSION, "watched": inst.id in watched, "sparkline": [b["close"] for b in inst.bars[-30:]], "broker_capable": False})
        return result

    @app.post(prefix + "/watchlists/{iid}", response_model=dto.WatchResult)
    def toggle_watch(iid: str, auth=Depends(identity), db=Depends(db_session)):
        if not db.get(Instrument, iid):
            raise HTTPException(404, "Instrument not found")
        watch = db.get(Watch, (auth.user_id, iid))
        if watch:
            db.delete(watch)
        else:
            db.add(Watch(user_id=auth.user_id, instrument_id=iid))
        db.commit()
        return {"watched": not bool(watch)}

    @app.get(prefix + "/market-data/{iid}", response_model=dto.MarketDataView)
    def market_data(iid: str, as_of: int | None = None, auth=Depends(identity), db=Depends(db_session)):
        inst = db.get(Instrument, iid)
        if not inst:
            raise HTTPException(404, "Instrument not found")
        bars = visible_bars(inst.bars, as_of)
        return {"instrument_id": iid, "bars": bars, "indicators": compute(bars), "source": DATASET_VERSION, "currency": "EUR", "interval": "1d", "mode": "DEMO", "as_of": as_of if as_of is not None else inst.bars[-1]["time"], "first_time": inst.bars[0]["time"], "last_time": inst.bars[-1]["time"], "total_bars": len(inst.bars), "quality": "Fictional fixture; synthetic weekday calendar"}

    @app.get(prefix + "/events", response_model=list[dto.EventView])
    def events(as_of: int | None = None, instrument_id: str | None = None, auth=Depends(identity), db=Depends(db_session)):
        return [{"id": event.id, "title": event.title, "domain": event.domain, "available_at": event.available_at, **event.payload} for event in db.scalars(select(Event).order_by(Event.available_at.desc())) if (as_of is None or datetime.fromisoformat(event.available_at).timestamp() <= as_of) and (instrument_id is None or instrument_id in event.payload["instrument_ids"])]

    @app.get(prefix + "/strategies", response_model=list[dto.StrategyView])
    def strategies(auth=Depends(identity), db=Depends(db_session)):
        return [record(s) for s in db.scalars(select(Strategy).order_by(Strategy.created_at.desc()))]

    @app.post(prefix + "/strategies", status_code=201, response_model=dto.StrategyView)
    def save_strategy(payload: StrategySpec, auth=Depends(identity), db=Depends(db_session)):
        if not db.get(Instrument, payload.instrument_id):
            raise HTTPException(404, "Instrument not found")
        sid = payload.strategy_id or str(uuid.uuid4())
        previous = db.scalar(select(Strategy).where(Strategy.strategy_id == sid).order_by(Strategy.version.desc()))
        if payload.strategy_id and (not previous or previous.author_id != auth.user_id):
            raise HTTPException(403, "Only the author can create another version; save a new strategy instead")
        spec = payload.model_dump(exclude={"strategy_id"})
        spec["status"] = "draft"
        strategy = Strategy(id=str(uuid.uuid4()), strategy_id=sid, version=previous.version + 1 if previous else 1, author_id=auth.user_id, spec=spec)
        db.add(strategy)
        db.add(Audit(actor_id=auth.user_id, action="STRATEGY_VERSION_SAVED", object_id=strategy.id, detail={"version": strategy.version}))
        db.commit()
        return record(strategy)

    def enqueue(db, uid, kind, payload):
        job = Job(id=str(uuid.uuid4()), user_id=uid, kind=kind, input=freeze_input(db, kind, payload))
        db.add(job)
        db.commit()
        app.state.runner.submit(job.id)
        return {"job_id": job.id, "status": "PENDING"}

    @app.post(prefix + "/backtests", status_code=202, response_model=dto.JobQueued)
    def backtest(payload: BacktestRequest, auth=Depends(identity), db=Depends(db_session)):
        if not db.get(Strategy, payload.strategy_version_id):
            raise HTTPException(404, "Strategy version not found")
        return enqueue(db, auth.user_id, "backtest", payload.model_dump())

    @app.post(prefix + "/research-runs", status_code=202, response_model=dto.JobQueued)
    def research(payload: ResearchRequest, auth=Depends(identity), db=Depends(db_session)):
        if not db.get(Instrument, payload.instrument_id):
            raise HTTPException(404, "Instrument not found")
        return enqueue(db, auth.user_id, "research", payload.model_dump())

    @app.get(prefix + "/jobs", response_model=list[dto.JobView])
    def jobs(auth=Depends(identity), db=Depends(db_session)):
        return [record(job) for job in db.scalars(select(Job).where(Job.user_id == auth.user_id).order_by(Job.created_at.desc()).limit(50))]

    @app.get(prefix + "/jobs/{jid}", response_model=dto.JobView)
    def job(jid: str, auth=Depends(identity), db=Depends(db_session)):
        job = db.get(Job, jid)
        if not job or job.user_id != auth.user_id:
            raise HTTPException(404, "Job not found")
        return record(job)

    @app.get(prefix + "/jobs/{jid}/snapshot", response_model=dto.InputSnapshot)
    def job_snapshot(jid: str, auth=Depends(identity), db=Depends(db_session)):
        job = db.get(Job, jid)
        if not job or job.user_id != auth.user_id:
            raise HTTPException(404, "Job not found")
        try:
            payload = verified_snapshot(job)
        except ValueError:
            raise ApiError(409, "SNAPSHOT_UNAVAILABLE", "This run has no verified frozen input. Submit a new run.")
        return {"job_id": job.id, "snapshot_hash": job.input["snapshot_hash"], "captured_at": job.input["captured_at"], "payload": payload}

    @app.get(prefix + "/accounts", response_model=list[dto.AccountView])
    def accounts(auth=Depends(identity), db=Depends(db_session)):
        return [record(account) for account in db.scalars(select(Account).where(Account.owner_id == auth.user_id))]

    @app.get(prefix + "/proposals", response_model=list[dto.ProposalView])
    def proposals(auth=Depends(identity), db=Depends(db_session)):
        return [record(p) for p in db.scalars(select(Proposal).where(Proposal.user_id == auth.user_id).order_by(Proposal.created_at.desc()))]

    @app.post(prefix + "/proposals", status_code=201, response_model=dto.ProposalView)
    def proposal(payload: ProposalRequest, auth=Depends(identity), db=Depends(db_session)):
        return record(create_proposal(db, auth.user_id, payload))

    @app.post(prefix + "/proposals/{pid}/approve", response_model=dto.ProposalView)
    def approval(pid: str, payload: ApprovalRequest, auth=Depends(identity), db=Depends(db_session)):
        return record(approve(db, auth.user_id, pid, payload.digest))

    @app.post(prefix + "/proposals/{pid}/reject", response_model=dto.RejectResult)
    def reject(pid: str, auth=Depends(identity), db=Depends(db_session)):
        proposal = db.get(Proposal, pid)
        if not proposal or proposal.user_id != auth.user_id:
            raise HTTPException(404, "Proposal not found")
        changed = db.execute(update(Proposal).where(Proposal.id == pid, Proposal.status == "AWAITING_APPROVAL").values(status="REJECTED"))
        if changed.rowcount != 1:
            raise HTTPException(409, "Proposal already processed")
        db.add(Audit(actor_id=auth.user_id, action="PROPOSAL_REJECTED", object_id=pid, detail={}))
        db.commit()
        return {"status": "REJECTED"}

    @app.post(prefix + "/accounts/kill-switch", response_model=dto.KillResult)
    def kill(payload: KillRequest, auth=Depends(identity), db=Depends(db_session)):
        db.execute(update(Account).where(Account.owner_id == auth.user_id).values(killed=int(payload.enabled), revision=Account.revision + 1))
        db.add(Audit(actor_id=auth.user_id, action="KILL_SWITCH_CHANGED", object_id=f"demo-{auth.user_id}", detail={"enabled": payload.enabled}))
        db.commit()
        return {"enabled": payload.enabled}

    @app.get(prefix + "/audit", response_model=list[dto.AuditView])
    def audit(auth=Depends(identity), db=Depends(db_session)):
        return [record(a) for a in db.scalars(select(Audit).where(Audit.actor_id.in_([auth.user_id, "system"])).order_by(Audit.id.desc()).limit(100))]

    @app.get(prefix + "/annotations/{iid}", response_model=list[dto.AnnotationView])
    def annotations(iid: str, as_of: int, auth=Depends(identity), db=Depends(db_session)):
        return [record(a) for a in db.scalars(select(Annotation).where(Annotation.user_id == auth.user_id, Annotation.instrument_id == iid, Annotation.as_of <= as_of).order_by(Annotation.created_at))]

    @app.post(prefix + "/annotations", response_model=dto.AnnotationView)
    def annotate(payload: AnnotationRequest, auth=Depends(identity), db=Depends(db_session)):
        inst = db.get(Instrument, payload.instrument_id)
        if not inst or payload.as_of not in {b["time"] for b in inst.bars}:
            raise HTTPException(422, "Invalid chart context")
        a = Annotation(id=str(uuid.uuid4()), user_id=auth.user_id, instrument_id=payload.instrument_id, as_of=payload.as_of, price=str(payload.price))
        db.add(a)
        db.commit()
        return record(a)

    @app.delete(prefix + "/annotations/{aid}", response_model=dto.Ok)
    def delete_annotation(aid: str, auth=Depends(identity), db=Depends(db_session)):
        a = db.get(Annotation, aid)
        if not a or a.user_id != auth.user_id:
            raise HTTPException(404, "Annotation not found")
        db.delete(a)
        db.commit()
        return {"ok": True}

    @app.get(prefix + "/notifications", response_model=list[dto.NotificationView])
    def notifications(auth=Depends(identity), db=Depends(db_session)):
        return [record(n) for n in db.scalars(select(Notification).where(Notification.user_id == auth.user_id).order_by(Notification.created_at.desc()).limit(50))]

    @app.post(prefix + "/notifications/{nid}/read", response_model=dto.Ok)
    def read_notification(nid: str, auth=Depends(identity), db=Depends(db_session)):
        n = db.get(Notification, nid)
        if not n or n.user_id != auth.user_id:
            raise HTTPException(404, "Notification not found")
        n.read = 1
        db.commit()
        return {"ok": True}

    @app.get(prefix + "/system-status", response_model=dto.SystemStatusView)
    def status(auth=Depends(identity)):
        return {"mode": "DEMO", "database": db_engine.dialect.name, "external_requests": False, "live_enabled": False, "timezone": "Europe/Berlin", "currency": "EUR", "worker": "Local single-process worker", "services": [
            {"name": "Demo market data", "status": "Ready", "detail": "Four fictional EUR instruments; frozen daily bars."},
            {"name": "Research graph", "status": "Ready", "detail": "LangGraph with deterministic evidence fixtures; zero model calls."},
            {"name": "vectorbt", "status": "Ready", "detail": "Actual numerical engine; background runs, next-bar signals, explicit costs."},
            {"name": "Local simulator", "status": "Ready", "detail": "Explicit approval and Decimal ledger; fixture snapshot fills only."},
            {"name": "OpenAI / external providers", "status": "Not implemented", "detail": "Credentials never activate external access. Adapter implementation remains pending."},
            {"name": "PostgreSQL / Redis / Chroma", "status": "Deferred", "detail": "Python and SQLite are the selected local runtime. Additional services are optional future work."},
            {"name": "LPPLS diagnostics", "status": "Pending", "detail": "Dependency probe only; no diagnostic output or probability claimed."},
            {"name": "External paper / live execution", "status": "Disabled", "detail": "No broker submission path is available."}]}

    dist = ROOT / "frontend" / "dist"
    if (dist / "assets").exists():
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")
    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        if path.startswith("api/"):
            raise HTTPException(404, "API route not found")
        if not (dist / "index.html").exists():
            return JSONResponse({"detail": "Frontend not built. Follow README setup."}, status_code=503)
        return FileResponse(dist / "index.html")
    return app


app = create_app()
