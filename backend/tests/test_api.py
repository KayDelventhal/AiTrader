from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import time
from sqlalchemy import select
from fastapi.testclient import TestClient
from app.core.security import utcnow
from app.db.models import Account, Proposal, Strategy, Audit
from app.db.seed import seed
from app.main import create_app
from conftest import sign_in

P = "/api/v1"


def proposal(client, **overrides):
    response = client.post(P + "/proposals", json={"instrument_id": "DEMO_NOVA", "side": "BUY", "quantity": 1, **overrides})
    assert response.status_code == 201, response.text
    return response.json()


def test_authentication_csrf_and_origin(client):
    assert client.get(P + "/accounts").status_code == 401
    assert client.post(P + "/auth/login", json={"username": "owner", "password": "bad"}).status_code == 401
    sign_in(client)
    client.headers.pop("X-CSRF-Token")
    assert client.post(P + "/accounts/kill-switch", json={"enabled": True}).status_code == 403
    assert client.post(P + "/auth/login", json={"username": "owner", "password": "local-demo-owner"}, headers={"Origin": "https://evil.example"}).status_code == 403
    response = client.get(P + "/auth/me")
    assert response.headers["cache-control"] == "no-store"


def test_login_cookie_and_logout(owner):
    assert owner.get(P + "/auth/me").json()["id"] == "owner"
    assert owner.post(P + "/auth/logout").status_code == 200
    assert owner.get(P + "/auth/me").status_code == 401


def test_idempotent_seed(owner, app):
    before = owner.get(P + "/instruments").json()
    with app.state.sessions() as db:
        seed(db); seed(db)
    assert owner.get(P + "/instruments").json() == before
    assert len(before) == 4


def test_private_account_isolation(owner):
    p = proposal(owner)
    sign_in(owner, "partner")
    assert owner.get(P + "/accounts").json()[0]["id"] == "demo-partner"
    assert owner.get(P + "/proposals").json() == []
    assert owner.post(P + f"/proposals/{p['id']}/approve", json={"digest": p["digest"]}).status_code == 404
    assert owner.post(P + f"/proposals/{p['id']}/reject").status_code == 404


def test_approval_hash_expiry_and_idempotency(owner, app):
    p = proposal(owner)
    assert owner.post(P + f"/proposals/{p['id']}/approve", json={"digest": "0" * 64}).status_code == 409
    filled = owner.post(P + f"/proposals/{p['id']}/approve", json={"digest": p["digest"]})
    assert filled.status_code == 200, filled.text
    balance = owner.get(P + "/accounts").json()[0]["cash"]
    assert owner.post(P + f"/proposals/{p['id']}/approve", json={"digest": p["digest"]}).status_code == 200
    assert owner.get(P + "/accounts").json()[0]["cash"] == balance
    assert len([a for a in owner.get(P + "/audit").json() if a["action"] == "LOCAL_FILL_APPROVED"]) == 1
    p2 = proposal(owner)
    with app.state.sessions() as db:
        db.get(Proposal, p2["id"]).expires_at = (utcnow() - timedelta(seconds=1)).isoformat(); db.commit()
    assert owner.post(P + f"/proposals/{p2['id']}/approve", json={"digest": p2["digest"]}).status_code == 409
    assert owner.get(P + "/proposals").json()[0]["status"] == "EXPIRED"


def test_payload_tampering_is_detected(owner, app):
    p = proposal(owner)
    with app.state.sessions() as db:
        row = db.get(Proposal, p["id"]); row.payload = {**row.payload, "quantity": 3}; db.commit()
    assert owner.post(P + f"/proposals/{p['id']}/approve", json={"digest": p["digest"]}).status_code == 409


def test_account_change_invalidates_other_proposals(owner):
    first, second = proposal(owner), proposal(owner)
    assert owner.post(P + f"/proposals/{first['id']}/approve", json={"digest": first["digest"]}).status_code == 200
    assert owner.post(P + f"/proposals/{second['id']}/approve", json={"digest": second["digest"]}).status_code == 409


def test_kill_switch_does_not_liquidate(owner):
    p = proposal(owner)
    owner.post(P + f"/proposals/{p['id']}/approve", json={"digest": p["digest"]})
    before = owner.get(P + "/accounts").json()[0]
    pending = proposal(owner)
    assert owner.post(P + "/accounts/kill-switch", json={"enabled": True}).status_code == 200
    after = owner.get(P + "/accounts").json()[0]
    assert before["positions"] == after["positions"] and before["cash"] == after["cash"]
    assert owner.post(P + f"/proposals/{pending['id']}/approve", json={"digest": pending["digest"]}).status_code == 409
    assert owner.post(P + "/proposals", json={"instrument_id": "DEMO_NOVA", "side": "BUY", "quantity": 1}).status_code == 409


def test_order_limits_and_shorting(owner):
    for body, expected in [({"instrument_id": "DEMO_NOVA", "side": "BUY", "quantity": 10}, 409), ({"instrument_id": "DEMO_NOVA", "side": "SELL", "quantity": 1}, 409), ({"instrument_id": "DEMO_NOVA", "side": "BUY", "quantity": -1}, 422), ({"instrument_id": "REAL_AAPL", "side": "BUY", "quantity": 1}, 404), ({"instrument_id": "DEMO_NOVA", "side": "BUY", "quantity": 1, "environment": "LIVE"}, 422)]:
        assert owner.post(P + "/proposals", json=body).status_code == expected


def test_two_simultaneous_approvals_do_not_double_spend(owner, app):
    first, second = proposal(owner), proposal(owner)
    def approve(p):
        c = TestClient(app, raise_server_exceptions=True)
        sign_in(c)
        response = c.post(P + f"/proposals/{p['id']}/approve", json={"digest": p["digest"]}).status_code
        c.close()
        return response
    # Independent client sessions, shared persistent database; the account CAS must win once.
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(approve, [first, second]))
    assert sorted(responses) == [200, 409]
    assert owner.get(P + "/accounts").json()[0]["positions"]["DEMO_NOVA"]["quantity"] == 1


def test_replay_and_evidence_cutoff(owner):
    full = owner.get(P + "/market-data/DEMO_NOVA").json()
    cutoff = full["bars"][50]["time"]
    partial = owner.get(P + f"/market-data/DEMO_NOVA?as_of={cutoff}").json()
    assert len(partial["bars"]) == 51
    assert all(p["time"] <= cutoff for series in partial["indicators"].values() for p in series)
    assert owner.get(P + f"/events?as_of={cutoff}").json() == []
    assert len(owner.get(P + "/events").json()) == 3


def test_strategy_versions_do_not_rewrite_old(owner):
    old = owner.get(P + "/strategies").json()[0]
    body = {k: v for k, v in old["spec"].items() if k != "status"}
    body.update(fast=10, strategy_id=old["strategy_id"])
    new = owner.post(P + "/strategies", json=body)
    assert new.status_code == 201, new.text
    assert new.json()["version"] == 2
    assert next(s for s in owner.get(P + "/strategies").json() if s["id"] == old["id"])["spec"]["fast"] == 20
    body["fast"] = 99
    assert owner.post(P + "/strategies", json=body).status_code == 422


def test_annotations_context_and_ownership(owner):
    bars = owner.get(P + "/market-data/DEMO_NOVA").json()["bars"]
    a = owner.post(P + "/annotations", json={"instrument_id": "DEMO_NOVA", "as_of": bars[-1]["time"], "price": "100.00"})
    assert a.status_code == 200
    assert owner.get(P + f"/annotations/DEMO_NOVA?as_of={bars[10]['time']}").json() == []
    assert owner.get(P + f"/annotations/DEMO_AURORA?as_of={bars[-1]['time']}").json() == []
    sign_in(owner, "partner")
    assert owner.delete(P + f"/annotations/{a.json()['id']}").status_code == 404


def test_research_job_and_no_evidence_result(owner):
    r = owner.post(P + "/research-runs", json={"instrument_id": "DEMO_NOVA", "as_of": 1})
    assert r.status_code == 202
    jid = r.json()["job_id"]
    for _ in range(100):
        job = owner.get(P + f"/jobs/{jid}").json()
        if job["status"] in {"SUCCEEDED", "FAILED"}: break
        time.sleep(.02)
    assert job["status"] == "SUCCEEDED", job
    assert job["result"]["evidence_ids"] == []
    assert job["result"]["model_calls"] == 0
    assert "Insufficient evidence" in job["result"]["conclusion"]
    sign_in(owner, "partner")
    assert owner.get(P + f"/jobs/{jid}").status_code == 404


def test_watchlist_and_notification_state(owner):
    response = owner.post(P + "/watchlists/DEMO_NOVA")
    assert response.json() == {"schema_version": "1", "watched": False}
    assert owner.post(P + "/watchlists/DEMO_NOVA").json() == {"schema_version": "1", "watched": True}
    assert owner.post(P + "/watchlists/UNKNOWN").status_code == 404
    assert owner.post(P + "/notifications/UNKNOWN/read").status_code == 404


def test_status_never_claims_broker_verification(owner):
    status = owner.get(P + "/system-status").json()
    assert status["external_requests"] is False
    assert status["live_enabled"] is False
    assert next(s for s in status["services"] if "External paper" in s["name"])["status"] == "Disabled"
    assert owner.get(P + "/missing-route").status_code == 404


def test_restart_preserves_fills_versions_and_audit(app):
    with TestClient(app) as first:
        sign_in(first)
        p = proposal(first)
        assert first.post(P + f"/proposals/{p['id']}/approve", json={"digest": p["digest"]}).status_code == 200
        expected_account = first.get(P + "/accounts").json()
        expected_versions = first.get(P + "/strategies").json()
    with TestClient(app) as restarted:
        sign_in(restarted)
        assert restarted.get(P + "/accounts").json() == expected_account
        assert restarted.get(P + "/strategies").json() == expected_versions
        assert restarted.get(P + "/proposals").json()[0]["status"] == "FILLED"
        assert len([a for a in restarted.get(P + "/audit").json() if a["action"] == "LOCAL_FILL_APPROVED"]) == 1


def test_rejected_proposal_cannot_be_approved(owner):
    p = proposal(owner)
    assert owner.post(P + f"/proposals/{p['id']}/reject").status_code == 200
    assert owner.post(P + f"/proposals/{p['id']}/approve", json={"digest": p["digest"]}).status_code == 409
    assert owner.get(P + "/accounts").json()[0]["cash"] == "10000.00"
