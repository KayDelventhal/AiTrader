"""Shared settings and operating expenses: real accounting, isolated databases."""
from decimal import Decimal
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from conftest import sign_in

P = "/api/v1"


def current_settings(client):
    response = client.get(P + "/workspace/settings")
    assert response.status_code == 200, response.text
    return response.json()


def change_settings(client, **changes):
    current = current_settings(client)
    payload = {
        "expected_revision": current["revision"],
        "markets": current["markets"],
        "horizon": current["horizon"],
        "monthly_limit_eur": current["monthly_limit_eur"],
        **changes,
    }
    return client.put(P + "/workspace/settings", json=payload)


def test_confirmed_defaults_are_shared_without_activating_services(owner):
    settings = current_settings(owner)
    assert set(settings["markets"]) == {"US", "EU"}
    assert settings["horizon"] == "days_weeks"
    assert Decimal(settings["monthly_limit_eur"]) == Decimal("20")
    assert settings["warning_pct"] == 80
    assert settings["can_manage"] is True
    status = owner.get(P + "/system-status").json()
    assert status["external_requests"] is False and status["live_enabled"] is False
    sign_in(owner, "partner")
    shared = current_settings(owner)
    assert shared["can_manage"] is False
    for key in ["markets", "horizon", "monthly_limit_eur", "revision"]:
        assert shared[key] == settings[key]


def test_explicit_settings_changes_are_versioned_and_reject_stale_writes(owner):
    old = current_settings(owner)
    response = change_settings(owner, horizon="weeks_months", monthly_limit_eur="25.00")
    assert response.status_code == 200, response.text
    updated = response.json()
    assert updated["revision"] == old["revision"] + 1
    assert updated["horizon"] == "weeks_months"
    assert Decimal(updated["monthly_limit_eur"]) == Decimal("25")
    stale = change_settings(owner, expected_revision=old["revision"], horizon="intraday")
    assert stale.status_code == 409
    assert current_settings(owner) == updated


def test_settings_mutation_requires_owner_and_csrf(owner):
    original = current_settings(owner)
    token = owner.headers.pop("X-CSRF-Token")
    assert change_settings(owner, horizon="intraday").status_code == 403
    owner.headers["X-CSRF-Token"] = token
    sign_in(owner, "partner")
    assert change_settings(owner, monthly_limit_eur="100.00").status_code == 403
    sign_in(owner)
    assert current_settings(owner) == original


@pytest.mark.parametrize("changes", [
    {"markets": []}, {"markets": ["CRYPTO"]}, {"horizon": "automatic"},
    {"monthly_limit_eur": "-1.00"}, {"monthly_limit_eur": "NaN"},
    {"monthly_limit_eur": "Infinity"}, {"enable_live_trading": True},
])
def test_invalid_settings_do_not_change_persisted_defaults(owner, changes):
    original = current_settings(owner)
    response = change_settings(owner, **changes)
    assert response.status_code == 422, response.text
    assert current_settings(owner) == original


def test_settings_survive_restart_and_do_not_rewrite_existing_strategies(app):
    with TestClient(app) as first:
        sign_in(first)
        strategies_before = first.get(P + "/strategies").json()
        response = change_settings(first, horizon="intraday", monthly_limit_eur="0.00")
        assert response.status_code == 200, response.text
        expected = response.json()
    with TestClient(app) as second:
        sign_in(second)
        assert current_settings(second) == expected
        assert second.get(P + "/strategies").json() == strategies_before


def test_workspace_settings_and_costs_require_sign_in(client):
    assert client.get(P + "/workspace/settings").status_code == 401
    assert client.get(P + "/costs").status_code == 401


def costs(client, month=None):
    response = client.get(P + "/costs", params={"month": month} if month else {})
    assert response.status_code == 200, response.text
    return response.json()


def add_expense(client, **changes):
    payload = {
        "idempotency_key": str(uuid4()), "provider": "Fixture provider",
        "category": "AI", "description": "Recorded provider invoice",
        "status": "CONFIRMED", "amount": "1.25", "currency": "EUR",
        "pricing_version": "test-pricing-v1", **changes,
    }
    return client.post(P + "/costs/entries", json=payload)


def reserve(client, **changes):
    payload = {
        "idempotency_key": str(uuid4()), "provider": "Fixture provider",
        "category": "AI", "description": "Bounded research request",
        "max_cost_eur": "5.00", **changes,
    }
    return client.post(P + "/costs/reservations", json=payload)


def settle(client, entry, **changes):
    return client.post(P + f"/costs/{entry['id']}/reconcile", json={
        "event_key": str(uuid4()), "expected_revision": entry["revision"],
        "status": "CONFIRMED", "amount": "2.00", "currency": "EUR",
        "pricing_version": "test-pricing-v1", "note": "Provider invoice received",
        **changes,
    })


def created(response):
    assert response.status_code in {200, 201}, response.text
    return response.json()


def test_cost_summary_distinguishes_actual_estimated_and_reserved(owner):
    created(add_expense(owner, amount="3.00"))
    created(add_expense(owner, status="ESTIMATED", amount="2.00", category="SEARCH_NEWS"))
    created(reserve(owner, max_cost_eur="4.00", category="MARKET_DATA"))
    summary = costs(owner)
    assert Decimal(summary["confirmed_eur"]) == Decimal("3")
    assert Decimal(summary["estimated_eur"]) == Decimal("2")
    assert Decimal(summary["reserved_eur"]) == Decimal("4")
    assert Decimal(summary["remaining_eur"]) == Decimal("11")
    assert len(summary["entries"]) == 3
    assert summary["has_unknown"] is False
    sign_in(owner, "partner")
    shared = costs(owner)
    assert shared["can_manage"] is False
    for key in ["confirmed_eur", "estimated_eur", "reserved_eur", "remaining_eur"]:
        assert shared[key] == summary[key]


def test_cost_changes_require_owner_and_csrf(owner):
    token = owner.headers.pop("X-CSRF-Token")
    assert add_expense(owner).status_code == 403
    owner.headers["X-CSRF-Token"] = token
    entry = created(reserve(owner))
    sign_in(owner, "partner")
    assert add_expense(owner).status_code == 403
    assert reserve(owner).status_code == 403
    assert settle(owner, entry).status_code == 403
    assert len(costs(owner)["entries"]) == 1


def test_reservation_exact_limit_and_late_bill_do_not_raise_budget(owner):
    first = created(reserve(owner, max_cost_eur="20.00"))
    assert reserve(owner, max_cost_eur="0.000001").status_code == 409
    before = current_settings(owner)
    late = created(settle(owner, first, amount="22.00"))
    assert late["status"] == "CONFIRMED"
    summary = costs(owner)
    assert Decimal(summary["confirmed_eur"]) == Decimal("22")
    assert Decimal(summary["remaining_eur"]) == Decimal("-2")
    assert Decimal(summary["available_eur"]) == Decimal("0")
    assert summary["status"] == "OVER_BUDGET"
    assert reserve(owner, max_cost_eur="0.01").status_code == 409
    assert current_settings(owner) == before


def test_cost_creation_idempotency_and_key_conflict(owner):
    key = str(uuid4())
    first = created(add_expense(owner, idempotency_key=key, amount="2.00"))
    again = created(add_expense(owner, idempotency_key=key, amount="2.00"))
    assert again["id"] == first["id"]
    assert add_expense(owner, idempotency_key=key, amount="3.00").status_code == 409
    summary = costs(owner)
    assert len(summary["entries"]) == 1
    assert Decimal(summary["confirmed_eur"]) == Decimal("2")


def test_reconciliation_is_idempotent_and_keeps_revision_history(owner):
    entry = created(reserve(owner, max_cost_eur="8.00"))
    event_key = str(uuid4())
    confirmed = created(settle(owner, entry, event_key=event_key, amount="3.00"))
    duplicate = created(settle(owner, entry, event_key=event_key, amount="3.00"))
    assert duplicate["id"] == confirmed["id"]
    assert duplicate["revision"] == confirmed["revision"]
    assert settle(owner, entry, event_key=event_key, amount="4.00").status_code == 409
    assert settle(owner, entry, amount="4.00").status_code == 409
    corrected = created(settle(owner, confirmed, amount="4.00", note="Corrected invoice"))
    assert corrected["revision"] == confirmed["revision"] + 1
    assert len(corrected["history"]) == 3
    assert [record["revision"] for record in corrected["history"]] == [1, 2, 3]
    assert corrected["history"][-1]["note"] == "Corrected invoice"
    assert Decimal(costs(owner)["confirmed_eur"]) == Decimal("4")


def test_unknown_expense_is_not_free_and_blocks_paid_admission(owner):
    entry = created(add_expense(owner, status="UNCERTAIN", amount=None))
    summary = costs(owner)
    assert summary["has_unknown"] is True
    assert reserve(owner, max_cost_eur="1.00").status_code == 409
    created(settle(owner, entry, amount="1.50"))
    assert costs(owner)["has_unknown"] is False
    created(reserve(owner, max_cost_eur="1.00"))


def test_timeout_retains_reservation_and_cancel_requires_explicit_reconciliation(owner):
    entry = created(reserve(owner, max_cost_eur="7.00"))
    uncertain = created(settle(owner, entry, status="UNCERTAIN", amount=None, note="Timed out; provider may have billed"))
    summary = costs(owner)
    assert Decimal(summary["reserved_eur"]) == Decimal("7")
    assert summary["has_unknown"] is True
    assert reserve(owner, max_cost_eur="1.00").status_code == 409
    created(settle(owner, uncertain, status="CANCELLED", amount=None, note="Provider confirmed no charge"))
    assert Decimal(costs(owner)["reserved_eur"]) == 0
    assert costs(owner)["has_unknown"] is False
    created(reserve(owner, max_cost_eur="20.00"))


def test_estimate_keeps_reserved_upper_bound_until_confirmed(owner):
    entry = created(reserve(owner, max_cost_eur="18.00"))
    estimated = created(settle(owner, entry, status="ESTIMATED", amount="2.00", note="Provisional usage only"))
    summary = costs(owner)
    assert Decimal(summary["estimated_eur"]) == Decimal("2")
    assert Decimal(summary["reserved_eur"]) == Decimal("16")
    assert Decimal(summary["remaining_eur"]) == Decimal("2")
    assert reserve(owner, max_cost_eur="3.00").status_code == 409
    created(settle(owner, estimated, amount="2.00"))
    created(reserve(owner, max_cost_eur="18.00"))


def test_reopening_confirmed_cost_as_unknown_blocks_spending(owner):
    entry = created(add_expense(owner, amount="15.00"))
    uncertain = created(settle(owner, entry, status="UNCERTAIN", amount=None, note="Invoice withdrawn pending correction"))
    summary = costs(owner)
    assert uncertain["amount_eur"] is None
    assert summary["has_unknown"] is True
    assert Decimal(summary["available_eur"]) == 0
    assert reserve(owner, max_cost_eur="0.01").status_code == 409
    assert Decimal(uncertain["history"][0]["payload"]["amount_eur"]) == Decimal("15")
    created(settle(owner, uncertain, amount="22.00"))
    assert costs(owner)["status"] == "OVER_BUDGET"


def test_cost_attribution_rejects_private_or_mismatched_runs(owner, app, monkeypatch):
    monkeypatch.setattr(app.state.runner, "submit", lambda jid: None)
    strategy = owner.get(P + "/strategies").json()[0]
    own_run = owner.post(P + "/backtests", json={"strategy_version_id": strategy["id"]}).json()["job_id"]
    research_run = owner.post(P + "/research-runs", json={"instrument_id": "DEMO_NOVA"}).json()["job_id"]
    sign_in(owner, "partner")
    private_run = owner.post(P + "/research-runs", json={"instrument_id": "DEMO_NOVA"}).json()["job_id"]
    sign_in(owner)
    assert add_expense(owner, run_id=private_run).status_code == 404
    assert add_expense(owner, run_id="missing-run").status_code == 404
    assert add_expense(owner, run_id=research_run, strategy_id=strategy["id"]).status_code == 422
    attributed = created(add_expense(owner, run_id=own_run, strategy_id=strategy["id"]))
    assert attributed["run_id"] == own_run
    assert attributed["strategy_id"] == strategy["id"]
    assert len(costs(owner)["entries"]) == 1


def test_decimal_expenses_and_original_currency_provenance(owner):
    for _ in range(3):
        created(add_expense(owner, amount="0.10"))
    foreign = created(add_expense(owner, amount="2.50", currency="USD", fx_rate="0.9", fx_as_of="2026-10-27T10:00:00Z"))
    assert foreign["currency"] == "USD"
    assert Decimal(foreign["original_amount"]) == Decimal("2.50")
    assert Decimal(foreign["fx_rate"]) == Decimal("0.9")
    assert foreign["fx_as_of"].startswith("2026-10-27T10:00:00")
    assert Decimal(foreign["amount_eur"]) == Decimal("2.25")
    assert Decimal(costs(owner)["confirmed_eur"]) == Decimal("2.55")
    assert add_expense(owner, amount="1.00", currency="USD").status_code == 422


@pytest.mark.parametrize("changes", [
    {"amount": "-1.00"}, {"amount": "NaN"}, {"amount": "Infinity"},
    {"amount": None, "status": "CONFIRMED"}, {"month": "2026-13"},
    {"currency": "USD", "fx_rate": "0", "fx_as_of": "2026-10-27T00:00:00Z"},
])
def test_invalid_expenses_cannot_poison_cost_totals(owner, changes):
    response = add_expense(owner, **changes)
    assert response.status_code == 422, response.text
    assert costs(owner)["entries"] == []


def test_lower_budget_keeps_committed_cost_and_blocks_new_requests(owner):
    created(reserve(owner, max_cost_eur="8.00"))
    assert change_settings(owner, monthly_limit_eur="5.00").status_code == 200
    summary = costs(owner)
    assert Decimal(summary["reserved_eur"]) == Decimal("8")
    assert Decimal(summary["limit_eur"]) == Decimal("5")
    assert reserve(owner, max_cost_eur="0.01").status_code == 409


def test_warning_threshold_counts_all_budget_categories(owner):
    created(add_expense(owner, amount="10.00", category="AI"))
    created(add_expense(owner, status="ESTIMATED", amount="3.00", category="SEARCH_NEWS"))
    created(reserve(owner, max_cost_eur="3.00", category="MARKET_DATA"))
    summary = costs(owner)
    assert summary["status"] == "WARNING"
    assert Decimal(summary["remaining_eur"]) == Decimal("4")
    assert {row["category"] for row in summary["breakdown"]} == {"AI", "SEARCH_NEWS", "MARKET_DATA"}


def test_unresolved_charges_survive_restart_without_release(app):
    with TestClient(app) as first:
        sign_in(first)
        entry = created(reserve(first, max_cost_eur="9.00"))
        created(settle(first, entry, status="UNCERTAIN", amount=None, note="Provider response lost"))
        expected = costs(first)
    with TestClient(app) as restarted:
        sign_in(restarted)
        assert costs(restarted) == expected
        assert reserve(restarted, max_cost_eur="1.00").status_code == 409


def test_month_uses_berlin_boundary_and_carries_unresolved_allowance(owner, monkeypatch):
    from app.workspace import service
    monkeypatch.setattr(service, "utcnow", lambda: datetime(2026, 10, 31, 22, 59, tzinfo=timezone.utc))
    previous = costs(owner)
    assert previous["month"] == "2026-10"
    entry = created(reserve(owner, max_cost_eur="8.00"))
    monkeypatch.setattr(service, "utcnow", lambda: datetime(2026, 10, 31, 23, 0, tzinfo=timezone.utc))
    current = costs(owner)
    assert current["month"] == "2026-11"
    assert Decimal(current["carryover_reserved_eur"]) == Decimal("8")
    assert reserve(owner, max_cost_eur="13.00").status_code == 409
    created(settle(owner, entry, amount="6.00"))
    assert Decimal(costs(owner, "2026-10")["confirmed_eur"]) == Decimal("6")
    assert Decimal(costs(owner)["carryover_reserved_eur"]) == 0


def test_unknown_prior_month_cost_blocks_new_month(owner, monkeypatch):
    from app.workspace import service
    monkeypatch.setattr(service, "utcnow", lambda: datetime(2026, 10, 20, tzinfo=timezone.utc))
    unknown = created(add_expense(owner, status="UNCERTAIN", amount=None))
    monkeypatch.setattr(service, "utcnow", lambda: datetime(2026, 11, 1, tzinfo=timezone.utc))
    assert costs(owner)["has_unknown"] is True
    assert reserve(owner, max_cost_eur="1.00").status_code == 409
    created(settle(owner, unknown, amount="2.00"))
    created(reserve(owner, max_cost_eur="1.00"))


def test_recurring_commitment_counts_once_each_month_and_stop_preserves_current(owner, monkeypatch):
    from app.workspace import service
    monkeypatch.setattr(service, "utcnow", lambda: datetime(2026, 10, 20, tzinfo=timezone.utc))
    payload = {"idempotency_key": "monthly-data", "provider": "Fixture exchange", "category": "MARKET_DATA", "description": "Monthly data commitment", "monthly_amount_eur": "6.00"}
    plan = created(owner.post(P + "/costs/recurring", json=payload))
    duplicate = created(owner.post(P + "/costs/recurring", json=payload))
    assert plan["id"] == duplicate["id"]
    for _ in range(3):
        summary = costs(owner)
        assert Decimal(summary["reserved_eur"]) == Decimal("6")
        assert len(summary["entries"]) == 1
    created(settle(owner, summary["entries"][0], amount="6.00"))
    monkeypatch.setattr(service, "utcnow", lambda: datetime(2026, 11, 2, tzinfo=timezone.utc))
    assert Decimal(costs(owner)["reserved_eur"]) == Decimal("6")
    assert reserve(owner, max_cost_eur="15.00").status_code == 409
    response = owner.post(P + f"/costs/recurring/{plan['id']}/stop", json={"expected_revision": plan["revision"], "event_key": "stop-monthly-data"})
    assert response.status_code == 200, response.text
    replay = owner.post(P + f"/costs/recurring/{plan['id']}/stop", json={"expected_revision": plan["revision"], "event_key": "stop-monthly-data"})
    assert replay.status_code == 200, replay.text
    assert replay.json() == response.json()
    assert Decimal(costs(owner)["reserved_eur"]) == Decimal("6")
    november = costs(owner)["entries"][0]
    created(settle(owner, november, amount="6.00"))
    monkeypatch.setattr(service, "utcnow", lambda: datetime(2026, 12, 2, tzinfo=timezone.utc))
    assert Decimal(costs(owner)["reserved_eur"]) == 0
    assert costs(owner)["entries"] == []


def test_old_month_limit_is_preserved_when_current_budget_changes(owner, monkeypatch):
    from app.workspace import service
    monkeypatch.setattr(service, "utcnow", lambda: datetime(2026, 10, 20, tzinfo=timezone.utc))
    # Do not materialize the old BudgetMonth first: history must still recover its limit.
    assert Decimal(current_settings(owner)["monthly_limit_eur"]) == Decimal("20")
    monkeypatch.setattr(service, "utcnow", lambda: datetime(2026, 11, 2, tzinfo=timezone.utc))
    assert change_settings(owner, monthly_limit_eur="30.00").status_code == 200
    assert Decimal(costs(owner)["limit_eur"]) == Decimal("30")
    assert Decimal(costs(owner, "2026-10")["limit_eur"]) == Decimal("20")
