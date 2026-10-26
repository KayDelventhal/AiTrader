import hashlib
import json
import uuid
from datetime import timedelta, datetime
from decimal import Decimal
from sqlalchemy import select, update
from fastapi import HTTPException
from app.core.config import settings
from app.core.security import utcnow
from app.db.models import Account, Instrument, Proposal, Audit
from app.simulation.ledger import money, book_fill


def digest(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def create_proposal(db, uid, request):
    account = db.get(Account, f"demo-{uid}")
    instrument = db.get(Instrument, request.instrument_id)
    if not instrument:
        raise HTTPException(404, "Instrument not found")
    if account.killed:
        raise HTTPException(409, "Kill switch is active")
    reference = instrument.bars[-1]
    price = money(Decimal(str(reference["close"])) * (Decimal("1.0005") if request.side == "BUY" else Decimal("0.9995")))
    fee = money(max(Decimal("1"), price * request.quantity * Decimal("0.001")))
    payload = {"schema_version": "1", "account_id": account.id, "account_revision": account.revision, "environment": "LOCAL_DEMO", "instrument_id": instrument.id, "symbol": instrument.symbol, "side": request.side, "quantity": request.quantity, "order_type": "FIXTURE_SNAPSHOT", "price": str(price), "fee": str(fee), "currency": "EUR", "source": "fictional-eur-daily-v1", "reference_time": reference["time"], "reference_price": str(reference["close"]), "fill_assumption": "Immediate fill at the frozen fixture close plus 5 bps slippage; not a live or next-open market fill."}
    _risk(account, payload)
    proposal = Proposal(id=str(uuid.uuid4()), user_id=uid, account_id=account.id, payload=payload, digest=digest(payload), expires_at=(utcnow() + timedelta(seconds=settings.approval_ttl_seconds)).isoformat())
    db.add(proposal)
    db.add(Audit(actor_id=uid, action="PROPOSAL_CREATED", object_id=proposal.id, detail={"digest": proposal.digest}))
    db.commit()
    return proposal


def _risk(account, payload):
    if account.killed:
        raise HTTPException(409, "Kill switch is active")
    if payload["environment"] != "LOCAL_DEMO" or not payload["instrument_id"].startswith("DEMO_"):
        raise HTTPException(409, "Only fictional local orders are supported")
    if payload["account_revision"] != account.revision:
        raise HTTPException(409, "Account changed. Create a new proposal.")
    amount = money(payload["price"]) * payload["quantity"]
    if amount + money(payload["fee"]) > settings.max_order_eur:
        raise HTTPException(409, "Demo order limit is EUR 500 including fees")
    position = account.positions.get(payload["instrument_id"], {"quantity": 0})
    if payload["side"] == "BUY" and (position["quantity"] + payload["quantity"]) * money(payload["price"]) > settings.max_position_eur:
        raise HTTPException(409, "Demo position limit is EUR 1,000")
    try:
        return book_fill(account.cash, account.positions, payload["instrument_id"], payload["side"], payload["quantity"], payload["price"], payload["fee"])
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


def approve(db, uid, pid, supplied_digest):
    proposal = db.get(Proposal, pid)
    if not proposal or proposal.user_id != uid:
        raise HTTPException(404, "Proposal not found")
    if supplied_digest != proposal.digest or digest(proposal.payload) != proposal.digest:
        raise HTTPException(409, "Approval hash mismatch")
    if proposal.status == "FILLED":
        return proposal  # A repeated approval returns the same completed operation.
    if proposal.status != "AWAITING_APPROVAL":
        raise HTTPException(409, "Proposal is not awaiting approval")
    if datetime.fromisoformat(proposal.expires_at) <= utcnow():
        proposal.status = "EXPIRED"
        db.commit()
        raise HTTPException(409, "Approval window expired. Create a new proposal.")
    account = db.scalar(select(Account).where(Account.id == proposal.account_id, Account.owner_id == uid).with_for_update())
    if account is None:
        raise HTTPException(404, "Account not found")
    cash, positions = _risk(account, proposal.payload)
    # Compare-and-swap prevents two parallel transactions spending the same revision,
    # including SQLite where SELECT FOR UPDATE is not available.
    changed = db.execute(update(Account).where(Account.id == account.id, Account.revision == account.revision, Account.killed == 0).values(cash=cash, positions=positions, revision=account.revision + 1))
    if changed.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "Concurrent account change. Review a new proposal.")
    claimed = db.execute(update(Proposal).where(Proposal.id == pid, Proposal.status == "AWAITING_APPROVAL").values(status="FILLED", fill={"id": f"fill-{pid}", "at": utcnow().isoformat(), **proposal.payload}))
    if claimed.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "Proposal already processed")
    db.add(Audit(actor_id=uid, action="LOCAL_FILL_APPROVED", object_id=pid, detail={"digest": supplied_digest, "cash_after": cash, "environment": "LOCAL_DEMO"}))
    db.commit()
    db.refresh(proposal)
    return proposal
