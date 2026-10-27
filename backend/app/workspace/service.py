"""Decimal cost ledger and short, serialized SQLite admission transactions.

The singleton write lock is taken before reading balances. It serializes admission,
settings changes, recurring commitments and reconciliation across all local workers.
External provider calls must happen AFTER a committed reservation, never while this
transaction is held. The ledger cannot activate a provider or submit an order.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal, ROUND_CEILING
import hashlib
import json
import re
import uuid
from zoneinfo import ZoneInfo

from sqlalchemy import select, update
from app.core.errors import ApiError
from app.core.security import utcnow
from app.db.models import (WorkspaceSettings, WorkspaceSettingsRevision, BudgetMonth,
                           CostEntry, CostRevision, RecurringCost, Audit, Job, Strategy)
from app.workspace.contracts import (WorkspaceSettingsUpdate, ManualCost, ReserveCost,
                                     ReconcileCost, RecurringCostCreate, StopRecurringCost)

MICROS = Decimal(1000000)
BERLIN = ZoneInfo("Europe/Berlin")


def current_month(now=None):
    return (now or utcnow()).astimezone(BERLIN).strftime("%Y-%m")


def _now():
    return utcnow().astimezone(timezone.utc).isoformat()


def money(micros):
    return format(Decimal(micros) / MICROS, ".6f")


def micros(value):
    return int((Decimal(value) * MICROS).to_integral_value(rounding=ROUND_CEILING))


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _request_hash(request):
    return _hash(request.model_dump(mode="json"))


def _owner(actor_id):
    if actor_id != "owner":
        raise ApiError(403, "WORKSPACE_OWNER_REQUIRED", "Only the workspace owner can change settings or costs.")


def seed_workspace(db):
    if db.get(WorkspaceSettings, 1) is None:
        db.add(WorkspaceSettings(id=1, revision=1, markets=["US", "EU"], horizon="days_weeks",
                                 monthly_limit_micros=20000000, warning_pct=80, updated_at=_now()))
        db.flush()
        db.add(WorkspaceSettingsRevision(revision=1, actor_id="system", created_at=_now(), payload=settings_snapshot(db)))
        db.commit()


def settings_snapshot(db):
    row = db.get(WorkspaceSettings, 1)
    if row is None:
        raise ApiError(503, "WORKSPACE_NOT_INITIALIZED", "Run migrations and the workspace seed first.")
    return {"schema_version": "1", "revision": row.revision, "markets": list(row.markets),
            "horizon": row.horizon, "monthly_limit_eur": money(row.monthly_limit_micros), "warning_pct": row.warning_pct}


def get_settings(db, user_id="owner"):
    return {**settings_snapshot(db), "can_manage": user_id == "owner"}


@contextmanager
def _locked(db):
    try:
        changed = db.execute(update(WorkspaceSettings).where(WorkspaceSettings.id == 1).values(revision=WorkspaceSettings.revision))
        if changed.rowcount != 1:
            raise ApiError(503, "WORKSPACE_NOT_INITIALIZED", "Run migrations and the workspace seed first.")
        # Discard any earlier cached settings/balances after acquiring the write lock.
        db.expire_all()
        yield
        db.commit()
    except BaseException:
        db.rollback()
        raise


def _valid_month(month, allow_future=False):
    month = month or current_month()
    if not re.fullmatch(r"(20\d{2}|2100)-(0[1-9]|1[0-2])", month):
        raise ApiError(422, "INVALID_MONTH", "Use a calendar month in YYYY-MM format.")
    if not allow_future and month > current_month():
        raise ApiError(422, "FUTURE_COST_MONTH", "Future expenses cannot be recorded as current spending.")
    return month


def _ensure_month(db, month):
    row = db.get(BudgetMonth, month)
    if row is None:
        history = list(db.scalars(select(WorkspaceSettingsRevision).order_by(WorkspaceSettingsRevision.revision)))
        # A historical month uses the last configuration effective in that month,
        # never a later raised limit. Before the first configuration use the initial limit.
        eligible = [h for h in history if current_month(datetime.fromisoformat(h.created_at)) <= month]
        snapshot = (eligible[-1] if eligible else history[0]).payload
        row = BudgetMonth(month=month, limit_micros=micros(snapshot["monthly_limit_eur"]),
                          settings_revision=snapshot["revision"], created_at=_now())
        db.add(row)
        db.flush()
    return row


def update_settings(db, actor_id, request: WorkspaceSettingsUpdate):
    _owner(actor_id)
    with _locked(db):
        row = db.get(WorkspaceSettings, 1)
        if row.revision != request.expected_revision:
            raise ApiError(409, "SETTINGS_CHANGED", "Workspace settings changed. Refresh before saving.")
        # Close every elapsed month under its existing configuration before changing defaults.
        _materialize_recurring(db, current_month())
        row.markets = sorted(request.markets)
        row.horizon = request.horizon
        row.monthly_limit_micros = micros(request.monthly_limit_eur)
        row.warning_pct = request.warning_pct
        row.revision += 1
        row.updated_at = _now()
        period = _ensure_month(db, current_month())
        period.limit_micros, period.settings_revision = row.monthly_limit_micros, row.revision
        db.flush()
        snapshot = settings_snapshot(db)
        db.add(WorkspaceSettingsRevision(revision=row.revision, actor_id=actor_id, created_at=_now(), payload=snapshot))
        db.add(Audit(actor_id=actor_id, action="WORKSPACE_SETTINGS_CHANGED", object_id="local-workspace", detail=snapshot))
        return {**snapshot, "can_manage": True}


def _entry_payload(entry):
    return {"month": entry.month, "provider": entry.provider, "category": entry.category,
            "description": entry.description, "status": entry.status,
            "amount_eur": money(entry.amount_micros) if entry.amount_micros is not None else None,
            "reserved_eur": money(entry.reserved_micros), "currency": entry.currency,
            "original_amount": entry.original_amount, "fx_rate": entry.fx_rate, "fx_as_of": entry.fx_as_of,
            "pricing_version": entry.pricing_version, "run_id": entry.run_id,
            "strategy_id": entry.strategy_id, "source": entry.source}


def entry_view(db, entry):
    history = db.scalars(select(CostRevision).where(CostRevision.entry_id == entry.id).order_by(CostRevision.revision))
    return {"schema_version": "1", "id": entry.id, **_entry_payload(entry), "revision": entry.revision,
            "created_at": entry.created_at, "history": [{"schema_version": "1", "revision": r.revision,
            "event_key": r.event_key, "actor_id": r.actor_id, "created_at": r.created_at,
            "note": r.note, "payload": r.payload} for r in history]}


def _revision(db, entry, actor_id, event_key, request_hash, note):
    db.flush()
    db.add(CostRevision(entry_id=entry.id, event_key=event_key, request_hash=request_hash,
                        revision=entry.revision, actor_id=actor_id, created_at=_now(), note=note, payload=_entry_payload(entry)))
    db.add(Audit(actor_id=actor_id, action="OPERATING_COST_RECORDED", object_id=entry.id,
                 detail={"revision": entry.revision, "month": entry.month, "status": entry.status}))
    db.flush()


def _existing(db, key, digest):
    entry = db.scalar(select(CostEntry).where(CostEntry.idempotency_key == key))
    if entry and entry.request_hash != digest:
        raise ApiError(409, "IDEMPOTENCY_CONFLICT", "This request key was already used with different values.")
    return entry


def _attribution(db, actor_id, run_id, strategy_id):
    if run_id:
        run = db.get(Job, run_id)
        if not run or run.user_id != actor_id:
            raise ApiError(404, "COST_RUN_NOT_FOUND", "An owned run is required for cost attribution.")
    if strategy_id:
        strategy = db.get(Strategy, strategy_id)
        if not strategy or strategy.author_id != actor_id:
            raise ApiError(404, "COST_STRATEGY_NOT_FOUND", "An owned strategy version is required for cost attribution.")
    if run_id and strategy_id and run.input.get("strategy_version_id") != strategy_id:
        raise ApiError(422, "COST_ATTRIBUTION_MISMATCH", "Run and strategy attribution must refer to the same version.")


def _amount_fields(request):
    rate = Decimal(1) if request.currency == "EUR" else request.fx_rate
    return {"amount_micros": micros(request.amount * rate) if request.amount is not None else None,
            "currency": request.currency, "original_amount": str(request.amount) if request.amount is not None else None,
            "fx_rate": str(rate) if rate is not None else None,
            "fx_as_of": request.fx_as_of.isoformat() if request.fx_as_of else None,
            "pricing_version": request.pricing_version}


def record_cost(db, actor_id, request: ManualCost):
    _owner(actor_id)
    digest = _request_hash(request)
    with _locked(db):
        existing = _existing(db, "manual:" + request.idempotency_key, digest)
        if existing:
            return entry_view(db, existing)
        month = _valid_month(request.month)
        _materialize_recurring(db, current_month())
        _ensure_month(db, month)
        _attribution(db, actor_id, request.run_id, request.strategy_id)
        entry = CostEntry(id=str(uuid.uuid4()), idempotency_key="manual:" + request.idempotency_key,
                          request_hash=digest, month=month, provider=request.provider, category=request.category,
                          description=request.description, status=request.status, reserved_micros=0,
                          source="manual", revision=1, created_at=_now(), run_id=request.run_id,
                          strategy_id=request.strategy_id, **_amount_fields(request))
        db.add(entry)
        _revision(db, entry, actor_id, "created", digest, "Manually recorded operating expense; no provider request was made.")
        return entry_view(db, entry)


def _parts(entry):
    amount = entry.amount_micros or 0
    if entry.status == "CONFIRMED":
        return amount, 0, 0, False
    if entry.status == "ESTIMATED":
        return 0, amount, max(0, entry.reserved_micros - amount), False
    if entry.status == "RESERVED":
        return 0, 0, entry.reserved_micros, False
    if entry.status == "UNCERTAIN":
        return 0, 0, entry.reserved_micros, True
    return 0, 0, 0, False


def _totals(db, month):
    entries = list(db.scalars(select(CostEntry).where(CostEntry.month == month).order_by(CostEntry.created_at.desc(), CostEntry.id)))
    previous = list(db.scalars(select(CostEntry).where(CostEntry.month < month, CostEntry.status.in_(["RESERVED", "UNCERTAIN", "ESTIMATED"]))))
    parts = [_parts(e) for e in entries]
    confirmed, estimated, reserved = (sum(p[i] for p in parts) for i in range(3))
    # Carry unresolved prior-month bounds into current admission. Once reconciled,
    # the final expense remains in its original month and this hold disappears.
    carry = sum(max(e.reserved_micros, e.amount_micros or 0) for e in previous)
    unknown = any(p[3] for p in parts) or any(e.status == "UNCERTAIN" for e in previous)
    return entries, confirmed, estimated, reserved, carry, unknown


def reserve_cost(db, actor_id, request: ReserveCost):
    _owner(actor_id)
    digest = _request_hash(request)
    with _locked(db):
        existing = _existing(db, "reservation:" + request.idempotency_key, digest)
        if existing:
            return entry_view(db, existing)
        month = current_month()
        _materialize_recurring(db, month)
        period = _ensure_month(db, month)
        _, confirmed, estimated, reserved, carry, unknown = _totals(db, month)
        if unknown:
            raise ApiError(409, "UNKNOWN_COST_BLOCKS_SPENDING", "Reconcile unknown costs before starting more paid work.")
        maximum = micros(request.max_cost_eur)
        if confirmed + estimated + reserved + carry + maximum > period.limit_micros:
            raise ApiError(409, "BUDGET_EXHAUSTED", "The remaining monthly budget cannot cover this reservation.")
        _attribution(db, actor_id, request.run_id, request.strategy_id)
        entry = CostEntry(id=str(uuid.uuid4()), idempotency_key="reservation:" + request.idempotency_key,
                          request_hash=digest, month=month, provider=request.provider, category=request.category,
                          description=request.description, status="RESERVED", amount_micros=None, reserved_micros=maximum,
                          currency="EUR", original_amount=None, fx_rate="1", fx_as_of=None,
                          pricing_version="bounded-reservation-v1", run_id=request.run_id,
                          strategy_id=request.strategy_id, source="reservation", revision=1, created_at=_now())
        db.add(entry)
        _revision(db, entry, actor_id, "created", digest, "Bounded budget reservation; no external request was started by this ledger.")
        return entry_view(db, entry)


def reconcile_cost(db, actor_id, entry_id, request: ReconcileCost):
    _owner(actor_id)
    digest = _request_hash(request)
    with _locked(db):
        entry = db.get(CostEntry, entry_id)
        if entry is None:
            raise ApiError(404, "COST_NOT_FOUND", "Cost entry not found.")
        event = db.scalar(select(CostRevision).where(CostRevision.entry_id == entry_id, CostRevision.event_key == request.event_key))
        if event:
            if event.request_hash != digest:
                raise ApiError(409, "IDEMPOTENCY_CONFLICT", "This reconciliation key was already used with different values.")
            return entry_view(db, entry)
        if entry.revision != request.expected_revision:
            raise ApiError(409, "COST_CHANGED", "The cost entry changed. Refresh before reconciling.")
        if request.status == "CANCELLED" and entry.status not in {"RESERVED", "UNCERTAIN"}:
            raise ApiError(409, "COST_CANNOT_CANCEL", "Record a corrected amount for an incurred expense; only uncharged reservations can be cancelled.")
        if request.status == "CANCELLED" and entry.source == "manual":
            raise ApiError(409, "COST_CANNOT_CANCEL", "Resolve a manually recorded expense with a confirmed amount, including zero when verified.")
        # Billing corrections can exceed a prior bound. Record reality and block
        # subsequent admission, instead of rejecting an inconvenient invoice.
        for key, value in _amount_fields(request).items():
            setattr(entry, key, value)
        if request.status in {"CONFIRMED", "CANCELLED"}:
            entry.reserved_micros = 0
        entry.status = request.status
        entry.revision += 1
        _revision(db, entry, actor_id, request.event_key, digest, request.note)
        return entry_view(db, entry)


def recurring_view(row):
    return {"schema_version": "1", "id": row.id, "provider": row.provider, "category": row.category,
            "description": row.description, "monthly_amount_eur": money(row.monthly_amount_micros),
            "start_month": row.start_month, "end_month": row.end_month, "revision": row.revision}


def _months(start, end):
    year, month = map(int, start.split("-"))
    while f"{year:04d}-{month:02d}" <= end:
        yield f"{year:04d}-{month:02d}"
        month += 1
        if month == 13:
            year, month = year + 1, 1


def _materialize_recurring(db, through):
    for recurring in db.scalars(select(RecurringCost)):
        end = min(through, recurring.end_month) if recurring.end_month else through
        for month in _months(recurring.start_month, end):
            key = f"recurring:{recurring.id}:{month}"
            digest = _hash({"id": recurring.id, "month": month, "amount": recurring.monthly_amount_micros})
            if _existing(db, key, digest):
                continue
            _ensure_month(db, month)
            entry = CostEntry(id=str(uuid.uuid4()), idempotency_key=key, request_hash=digest, month=month,
                              provider=recurring.provider, category=recurring.category, description=recurring.description,
                              status="RESERVED", amount_micros=None, reserved_micros=recurring.monthly_amount_micros,
                              currency="EUR", original_amount=None, fx_rate="1", fx_as_of=None,
                              pricing_version="manual-monthly-commitment-v1", run_id=None, strategy_id=None,
                              source="recurring", revision=1, created_at=_now())
            db.add(entry)
            _revision(db, entry, "system", "created", digest, "Monthly commitment recorded once; no subscription was purchased.")


def create_recurring(db, actor_id, request: RecurringCostCreate):
    _owner(actor_id)
    digest = _request_hash(request)
    with _locked(db):
        existing = db.scalar(select(RecurringCost).where(RecurringCost.idempotency_key == request.idempotency_key))
        if existing:
            if existing.request_hash != digest:
                raise ApiError(409, "IDEMPOTENCY_CONFLICT", "This commitment key was already used with different values.")
            return recurring_view(existing)
        start = _valid_month(request.start_month, allow_future=True)
        if start < current_month():
            raise ApiError(422, "PAST_RECURRING_START", "Record past invoices separately; new recurring commitments start this month or later.")
        row = RecurringCost(id=str(uuid.uuid4()), idempotency_key=request.idempotency_key, request_hash=digest,
                            provider=request.provider, category=request.category, description=request.description,
                            monthly_amount_micros=micros(request.monthly_amount_eur), start_month=start,
                            end_month=None, revision=1, created_at=_now())
        db.add(row)
        db.flush()
        _materialize_recurring(db, current_month())
        db.add(Audit(actor_id=actor_id, action="RECURRING_COST_RECORDED", object_id=row.id, detail=recurring_view(row)))
        return recurring_view(row)


def stop_recurring(db, actor_id, recurring_id, request: StopRecurringCost):
    _owner(actor_id)
    digest = _request_hash(request)
    with _locked(db):
        row = db.get(RecurringCost, recurring_id)
        if row is None:
            raise ApiError(404, "RECURRING_COST_NOT_FOUND", "Recurring cost not found.")
        if row.stop_event_key == request.event_key:
            if row.stop_request_hash != digest:
                raise ApiError(409, "IDEMPOTENCY_CONFLICT", "This stop key was already used with different values.")
            return recurring_view(row)
        if row.revision != request.expected_revision or row.end_month:
            raise ApiError(409, "RECURRING_COST_CHANGED", "The recurring commitment changed. Refresh before saving.")
        _materialize_recurring(db, current_month())
        row.end_month = current_month()
        row.revision += 1
        row.stop_event_key, row.stop_request_hash = request.event_key, digest
        db.add(Audit(actor_id=actor_id, action="RECURRING_COST_STOPPED", object_id=row.id, detail=recurring_view(row)))
        return recurring_view(row)


def cost_summary(db, month=None, user_id="owner"):
    month = _valid_month(month)
    with _locked(db):
        _materialize_recurring(db, current_month())
        period = _ensure_month(db, month)
        entries, confirmed, estimated, reserved, carry, unknown = _totals(db, month)
        remaining = period.limit_micros - confirmed - estimated - reserved - carry
        warning = db.get(WorkspaceSettings, 1).warning_pct
        if unknown:
            status = "UNKNOWN_COST"
        elif remaining < 0:
            status = "OVER_BUDGET"
        elif remaining == 0:
            status = "EXHAUSTED"
        elif (confirmed + estimated + reserved + carry) * 100 >= period.limit_micros * warning:
            status = "WARNING"
        else:
            status = "OK"
        groups = {}
        for entry in entries:
            key = (entry.provider, entry.category)
            values = groups.setdefault(key, [0, 0, 0, False])
            for i, value in enumerate(_parts(entry)):
                values[i] = (values[i] or value) if i == 3 else values[i] + value
        return {"schema_version": "1", "month": month, "current_month": current_month(), "limit_eur": money(period.limit_micros),
                "confirmed_eur": money(confirmed), "estimated_eur": money(estimated), "reserved_eur": money(reserved),
                "carryover_reserved_eur": money(carry), "remaining_eur": money(remaining),
                "available_eur": money(0 if unknown else max(0, remaining)), "status": status, "has_unknown": unknown,
                "can_manage": user_id == "owner", "entries": [entry_view(db, e) for e in entries],
                "breakdown": [{"schema_version": "1", "provider": k[0], "category": k[1],
                               "confirmed_eur": money(v[0]), "estimated_eur": money(v[1]), "reserved_eur": money(v[2]),
                               "has_unknown": v[3]} for k, v in sorted(groups.items())],
                "recurring": [recurring_view(r) for r in db.scalars(select(RecurringCost).order_by(RecurringCost.created_at.desc()))]}
