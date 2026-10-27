"""Compare a private demo ledger with shared expenses without claiming live profit."""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Literal
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.core.security import utcnow
from app.db.models import Account, Instrument, Proposal, CostEntry, Job
from app.core.errors import ApiError
from app.domain.responses import ResponseModel, DecimalString
from app.simulation.ledger import book_fill, money
from app.workspace.service import cost_summary


class PerformanceCostView(ResponseModel):
    month: str
    environment: Literal["LOCAL_DEMO"] = "LOCAL_DEMO"
    account_id: str
    realized_pnl_eur: DecimalString | None
    unrealized_pnl_eur: DecimalString | None
    valuation_basis: str
    operating_confirmed_eur: DecimalString
    operating_estimated_eur: DecimalString
    reserved_eur: DecimalString
    has_unknown_cost: bool
    illustrative_net_eur: DecimalString | None
    cost_allocation: Literal["FULL_WORKSPACE_SCENARIO"] = "FULL_WORKSPACE_SCENARIO"
    live_performance_available: Literal[False] = False
    notes: list[str]


class RunCostView(ResponseModel):
    job_id: str
    confirmed_eur: DecimalString
    estimated_eur: DecimalString
    reserved_eur: DecimalString
    has_unknown: bool
    entry_count: int
    scope: Literal["ATTRIBUTED_RECORDS_ONLY"] = "ATTRIBUTED_RECORDS_ONLY"


def run_costs(db, user_id, job_id):
    job = db.get(Job, job_id)
    if not job or job.user_id != user_id:
        raise ApiError(404, "JOB_NOT_FOUND", "Job not found")
    entries = list(db.scalars(select(CostEntry).where(CostEntry.run_id == job_id)))
    totals = {"confirmed_eur": Decimal(0), "estimated_eur": Decimal(0), "reserved_eur": Decimal(0)}
    unknown = False
    for entry in entries:
        amount = Decimal(entry.amount_micros or 0) / Decimal(1000000)
        bound = Decimal(entry.reserved_micros) / Decimal(1000000)
        if entry.status == "CONFIRMED":
            totals["confirmed_eur"] += amount
        elif entry.status == "ESTIMATED":
            totals["estimated_eur"] += amount
            totals["reserved_eur"] += max(Decimal(0), bound - amount)
        elif entry.status in {"RESERVED", "UNCERTAIN"}:
            totals["reserved_eur"] += bound
            unknown |= entry.status == "UNCERTAIN"
    return {"job_id": job_id, **{key: format(value, ".6f") for key, value in totals.items()},
            "has_unknown": unknown, "entry_count": len(entries)}


def month_bounds(month):
    year, month_number = map(int, month.split("-"))
    start = datetime(year, month_number, 1, tzinfo=ZoneInfo("Europe/Berlin"))
    end = datetime(year + (month_number == 12), month_number % 12 + 1, 1, tzinfo=start.tzinfo)
    return start.astimezone(timezone.utc), end.astimezone(timezone.utc)


def realized(positions):
    return sum((Decimal(p["realized_pnl"]) for p in positions.values()), Decimal(0))


def performance_cost_impact(db, user_id, month=None):
    summary = cost_summary(db, month, user_id)
    start, end = month_bounds(summary["month"])
    account = db.get(Account, f"demo-{user_id}")
    notes = [
        "Fictional local fills only; no live trading performance is available.",
        "Comparison subtracts the full shared workspace expenses from this account's demo realized P&L. It is not a per-user cost allocation or proof of AI-generated profit.",
        "Execution fees and slippage are already included in trading P&L. Reservations are commitments, not incurred expenses.",
    ]
    positions, cash, before = {}, "10000.00", Decimal(0)
    ledger_valid = True
    rows = list(db.scalars(select(Proposal).where(Proposal.user_id == user_id, Proposal.status == "FILLED")))
    try:
        # Event time, not proposal creation order, determines the accounting order.
        fills = sorted((row.fill for row in rows), key=lambda f: (datetime.fromisoformat(f["at"]), f["id"]))
        for fill in fills:
            at = datetime.fromisoformat(fill["at"])
            if at >= end:
                break
            cash, positions = book_fill(cash, positions, fill["instrument_id"], fill["side"], fill["quantity"], fill["price"], fill["fee"])
            if at < start:
                before = realized(positions)
        if summary["month"] == summary["current_month"] and (positions != account.positions or money(cash) != money(account.cash)):
            ledger_valid = False
            notes.append("The saved fills do not reconstruct the current account. Performance is unavailable until the ledger is reconciled.")
    except (KeyError, TypeError, ValueError):
        ledger_valid = False
        notes.append("Some saved fills cannot be reconstructed; performance is unavailable.")
    pnl = realized(positions) - before if ledger_valid else None
    valuation_cutoff = min(end, utcnow())
    unrealized = Decimal(0) if ledger_valid else None
    for iid, position in positions.items():
        if not position["quantity"] or unrealized is None:
            continue
        instrument = db.get(Instrument, iid)
        bars = [b for b in instrument.bars if datetime.fromisoformat(b["available_at"]) < valuation_cutoff] if instrument else []
        if not bars:
            unrealized = None
            notes.append("A position has no eligible fixture valuation; unrealized P&L is unavailable.")
            break
        unrealized += Decimal(str(bars[-1]["close"])) * position["quantity"] - Decimal(position["cost_basis"])
    expenses = Decimal(summary["confirmed_eur"]) + Decimal(summary["estimated_eur"])
    net = pnl - expenses if pnl is not None and not summary["has_unknown"] else None
    if summary["has_unknown"]:
        notes.append("Unpriced expenses are present. A complete result after operating expenses cannot be calculated.")
    if Decimal(summary["estimated_eur"]):
        notes.append("Operating expenses include estimates; the comparison will change after billing reconciliation.")
    return {
        "month": summary["month"], "account_id": account.id,
        "realized_pnl_eur": str(money(pnl)) if pnl is not None else None,
        "unrealized_pnl_eur": str(money(unrealized)) if unrealized is not None else None,
        "valuation_basis": "Latest available fictional fixture close before the selected period ends; unrealized P&L is excluded from the net comparison.",
        "operating_confirmed_eur": summary["confirmed_eur"], "operating_estimated_eur": summary["estimated_eur"],
        "reserved_eur": str(Decimal(summary["reserved_eur"]) + Decimal(summary["carryover_reserved_eur"])),
        "has_unknown_cost": summary["has_unknown"], "illustrative_net_eur": format(net, ".6f") if net is not None else None,
        "notes": notes,
    }
