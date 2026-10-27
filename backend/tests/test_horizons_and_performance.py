from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import select

from app.db.models import Account, Job, Proposal, Strategy
from app.reporting.cost_impact import month_bounds
from app.simulation.ledger import book_fill
from conftest import sign_in

P = "/api/v1"


def save_strategy(client, **overrides):
    request = {"name": "Versioned horizon", "hypothesis": "An explicitly saved holding period is independent of chart interval.", "instrument_id": "DEMO_NOVA", **overrides}
    response = client.post(P + "/strategies", json=request)
    assert response.status_code == 201, response.text
    return response.json()


def change_horizon(owner, value):
    current = owner.get(P + "/workspace/settings").json()
    response = owner.put(P + "/workspace/settings", json={"expected_revision": current["revision"], "markets": current["markets"], "horizon": value, "monthly_limit_eur": current["monthly_limit_eur"], "warning_pct": current["warning_pct"]})
    assert response.status_code == 200, response.text


def test_strategy_horizon_changes_only_on_new_versions(owner):
    original = save_strategy(owner)
    assert original["spec"]["horizon"] == "days_weeks"
    change_horizon(owner, "weeks_months")
    new = save_strategy(owner, strategy_id=original["strategy_id"])
    assert new["spec"]["horizon"] == "weeks_months"
    history = owner.get(P + "/strategies").json()
    assert next(s for s in history if s["id"] == original["id"])["spec"]["horizon"] == "days_weeks"
    explicit = save_strategy(owner, horizon="intraday")
    assert explicit["spec"]["horizon"] == "intraday"


def test_queued_jobs_keep_settings_and_strategy_horizons(owner, app, monkeypatch):
    monkeypatch.setattr(app.state.runner, "submit", lambda _: None)
    strategy = save_strategy(owner, horizon="weeks_months")
    backtest = owner.post(P + "/backtests", json={"strategy_version_id": strategy["id"]}).json()["job_id"]
    research = owner.post(P + "/research-runs", json={"instrument_id": "DEMO_NOVA"}).json()["job_id"]
    before = owner.get(P + f"/jobs/{research}/snapshot").json()
    assert before["payload"]["horizon"] == "days_weeks"
    change_horizon(owner, "intraday")
    assert owner.get(P + f"/jobs/{research}/snapshot").json() == before
    frozen = owner.get(P + f"/jobs/{backtest}/snapshot").json()
    assert frozen["payload"]["horizon"] == "weeks_months"
    assert frozen["payload"]["workspace_settings"]["horizon"] == "days_weeks"
    app.state.runner.run(research)
    assert owner.get(P + f"/jobs/{research}").json()["input"]["horizon"] == "days_weeks"


def test_legacy_strategy_horizon_is_not_rewritten(owner, app, monkeypatch):
    monkeypatch.setattr(app.state.runner, "submit", lambda _: None)
    with app.state.sessions() as db:
        legacy = db.get(Strategy, "strategy-trend-v1")
        spec = dict(legacy.spec)
        spec.pop("horizon", None)
        legacy.spec = spec
        db.commit()
    change_horizon(owner, "intraday")
    jid = owner.post(P + "/backtests", json={"strategy_version_id": "strategy-trend-v1"}).json()["job_id"]
    frozen = owner.get(P + f"/jobs/{jid}/snapshot").json()["payload"]
    assert frozen["horizon"] is None
    assert "horizon" not in frozen["strategy"]


def test_month_boundaries_use_berlin_even_across_dst():
    start, end = month_bounds("2026-10")
    assert start == datetime(2026, 9, 30, 22, tzinfo=timezone.utc)
    assert end == datetime(2026, 10, 31, 23, tzinfo=timezone.utc)
    assert month_bounds("2026-12")[1] == datetime(2026, 12, 31, 23, tzinfo=timezone.utc)


def add_fill(db, uid, ident, side, quantity, price, fee, when, cash, positions):
    cash, positions = book_fill(cash, positions, "DEMO_NOVA", side, quantity, price, fee)
    payload = {"id": ident, "at": when, "instrument_id": "DEMO_NOVA", "side": side, "quantity": quantity, "price": price, "fee": fee}
    db.add(Proposal(id=ident, user_id=uid, account_id=f"demo-{uid}", status="FILLED", payload={}, digest="a" * 64, expires_at=when, fill=payload))
    account = db.get(Account, f"demo-{uid}")
    account.cash, account.positions = cash, positions
    return cash, positions


def test_period_pnl_includes_prior_cost_basis_and_no_double_fee(owner, app):
    with app.state.sessions() as db:
        cash, positions = add_fill(db, "owner", "buy-before", "BUY", 2, "100", "1", "2026-09-20T10:00:00+00:00", "10000.00", {})
        add_fill(db, "owner", "sell-in-month", "SELL", 2, "110", "1", "2026-10-10T10:00:00+00:00", cash, positions)
        db.commit()
    response = owner.get(P + "/performance/cost-impact?month=2026-10")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["realized_pnl_eur"] == "18.00"
    assert Decimal(body["illustrative_net_eur"]) == 18
    assert body["unrealized_pnl_eur"] == "0.00"
    assert body["live_performance_available"] is False
    assert body["environment"] == "LOCAL_DEMO"
    assert owner.get(P + "/performance/cost-impact?month=2026-09").json()["realized_pnl_eur"] == "0.00"
    sign_in(owner, "partner")
    assert owner.get(P + "/performance/cost-impact?month=2026-10").json()["realized_pnl_eur"] == "0.00"


def test_account_mismatch_is_unavailable_instead_of_invented_profit(owner, app):
    with app.state.sessions() as db:
        db.get(Account, "demo-owner").cash = "10001.00"
        db.commit()
    body = owner.get(P + "/performance/cost-impact").json()
    assert body["realized_pnl_eur"] is None
    assert body["illustrative_net_eur"] is None
    assert any("reconciled" in note for note in body["notes"])


def test_run_cost_attribution_is_private_and_not_double_counted(owner, app, monkeypatch):
    monkeypatch.setattr(app.state.runner, "submit", lambda _: None)
    jid = owner.post(P + "/research-runs", json={"instrument_id": "DEMO_NOVA"}).json()["job_id"]
    empty = owner.get(P + f"/jobs/{jid}/costs").json()
    assert empty["entry_count"] == 0
    request = {"provider": "Fixture invoice", "category": "AI", "description": "Attributed analysis", "amount": "1.234567", "status": "CONFIRMED", "pricing_version": "test-invoice", "idempotency_key": "attributed", "run_id": jid}
    assert owner.post(P + "/costs/entries", json=request).status_code == 201
    assert owner.post(P + "/costs/entries", json=request).status_code == 201
    totals = owner.get(P + f"/jobs/{jid}/costs").json()
    assert totals["entry_count"] == 1
    assert totals["confirmed_eur"] == "1.234567"
    assert owner.get(P + "/costs").json()["confirmed_eur"] == "1.234567"
    assert owner.get(P + "/performance/cost-impact").json()["illustrative_net_eur"] == "-1.234567"
    sign_in(owner, "partner")
    assert owner.get(P + f"/jobs/{jid}/costs").status_code == 404


def test_performance_excludes_reservations_and_refuses_unknown_net(owner):
    reservation = {"provider": "Reserved service", "category": "AI", "description": "Future bounded work", "max_cost_eur": "5", "idempotency_key": "future-work"}
    assert owner.post(P + "/costs/reservations", json=reservation).status_code == 201
    report = owner.get(P + "/performance/cost-impact").json()
    assert Decimal(report["illustrative_net_eur"]) == 0
    assert Decimal(report["reserved_eur"]) == 5
    unknown = {"provider": "Unknown service", "category": "SEARCH_NEWS", "description": "Invoice unavailable", "status": "UNCERTAIN", "pricing_version": "unknown", "idempotency_key": "unknown-net"}
    assert owner.post(P + "/costs/entries", json=unknown).status_code == 201
    report = owner.get(P + "/performance/cost-impact").json()
    assert report["has_unknown_cost"] is True
    assert report["illustrative_net_eur"] is None
