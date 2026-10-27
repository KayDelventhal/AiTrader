"""Race tests use independent authenticated sessions against one SQLite database."""
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier

from fastapi.testclient import TestClient

from conftest import sign_in
from test_workspace_costs import P, costs, created, reserve, settle, current_settings


def competing_requests(app, requests):
    barrier = Barrier(len(requests))

    def perform(request):
        client = TestClient(app, raise_server_exceptions=True)
        try:
            sign_in(client)
            barrier.wait(timeout=10)
            return request(client)
        finally:
            client.close()

    with ThreadPoolExecutor(max_workers=len(requests)) as pool:
        return list(pool.map(perform, requests))


def test_concurrent_agents_cannot_reserve_the_same_remaining_budget(owner, app):
    costs(owner)
    responses = competing_requests(app, [
        lambda client: reserve(client, idempotency_key="agent-one", max_cost_eur="12.00"),
        lambda client: reserve(client, idempotency_key="agent-two", max_cost_eur="12.00"),
    ])
    assert sorted(r.status_code for r in responses) == [201, 409]
    summary = costs(owner)
    assert Decimal(summary["reserved_eur"]) == Decimal("12")
    assert Decimal(summary["remaining_eur"]) == Decimal("8")
    assert len(summary["entries"]) == 1


def test_concurrent_retry_of_same_request_reserves_only_once(owner, app):
    costs(owner)
    responses = competing_requests(app, [
        lambda client: reserve(client, idempotency_key="same-request", max_cost_eur="8.00"),
        lambda client: reserve(client, idempotency_key="same-request", max_cost_eur="8.00"),
    ])
    entries = [created(response) for response in responses]
    assert entries[0]["id"] == entries[1]["id"]
    summary = costs(owner)
    assert Decimal(summary["reserved_eur"]) == Decimal("8")
    assert len(summary["entries"]) == 1


def test_concurrent_conflicting_reconciliations_cannot_overwrite_each_other(owner, app):
    entry = created(reserve(owner, max_cost_eur="10.00"))
    responses = competing_requests(app, [
        lambda client: settle(client, entry, event_key="invoice-one", amount="4.00"),
        lambda client: settle(client, entry, event_key="invoice-two", amount="5.00"),
    ])
    assert sorted(r.status_code for r in responses) == [200, 409]
    summary = costs(owner)
    assert Decimal(summary["confirmed_eur"]) in {Decimal("4"), Decimal("5")}
    assert Decimal(summary["reserved_eur"]) == 0
    assert len(summary["entries"]) == 1


def test_budget_lowering_and_new_reservation_have_a_serial_outcome(owner, app):
    settings = current_settings(owner)
    update = {"expected_revision": settings["revision"], "markets": settings["markets"], "horizon": settings["horizon"], "monthly_limit_eur": "10.00"}
    responses = competing_requests(app, [
        lambda client: reserve(client, idempotency_key="racing-reservation", max_cost_eur="12.00"),
        lambda client: client.put(P + "/workspace/settings", json=update),
    ])
    assert responses[1].status_code == 200, responses[1].text
    summary = costs(owner)
    assert Decimal(summary["limit_eur"]) == Decimal("10")
    if responses[0].status_code == 201:
        # Admission preceded the explicit reduction; existing commitments are preserved.
        assert Decimal(summary["reserved_eur"]) == Decimal("12")
        assert summary["status"] == "OVER_BUDGET"
        assert reserve(owner, max_cost_eur="0.01").status_code == 409
    else:
        assert responses[0].status_code == 409, responses[0].text
        assert Decimal(summary["reserved_eur"]) == 0
