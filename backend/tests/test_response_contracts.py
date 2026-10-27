import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError, OperationalError
from app.domain.responses import Health

P = "/api/v1"


def test_every_public_operation_has_success_and_error_contracts(app):
    schema = app.openapi()
    for path, methods in schema["paths"].items():
        assert path.startswith(P)
        for operation in methods.values():
            successes = [r for code, r in operation["responses"].items() if code.startswith("2")]
            assert successes and all(r["content"]["application/json"]["schema"] for r in successes)
            assert operation["responses"]["422"]["content"]["application/json"]["schema"]["$ref"].endswith("/ErrorResponse")


def test_validation_does_not_echo_secrets(client):
    secret = "must-never-return-this-password"
    response = client.post(P + "/auth/login", json={"username": "owner", "password": {"secret": secret}})
    assert response.status_code == 422
    assert secret not in response.text
    body = response.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert body["issues"] == [{"location": ["body", "password"], "code": "string_type"}]
    assert body["request_id"] == response.headers["X-Request-ID"]
    assert response.headers["Cache-Control"] == "no-store"


@pytest.mark.parametrize("exception,status,code", [
    (IntegrityError("secret SQL", {}, Exception("credential")), 409, "CONCURRENT_CHANGE"),
    (OperationalError("secret SQL", {}, Exception("credential")), 503, "DATABASE_UNAVAILABLE"),
    (HTTPException(404, "Record not found"), 404, "NOT_FOUND"),
])
def test_errors_use_stable_codes_and_request_ids(client, app, exception, status, code):
    @app.get("/contract-test-error")
    def fail():
        raise exception
    # Register before the SPA catch-all so the deliberately failing route runs.
    app.router.routes.insert(0, app.router.routes.pop())
    response = client.get("/contract-test-error")
    assert response.status_code == status
    assert response.json()["code"] == code
    assert response.json()["request_id"] == response.headers["X-Request-ID"]
    assert "secret SQL" not in response.text and "credential" not in response.text


def test_invalid_responses_are_redacted(client, app):
    @app.get("/contract-test-response", response_model=Health)
    def invalid():
        return {"status": "secret-invalid-status", "private_key": "not-public"}
    app.router.routes.insert(0, app.router.routes.pop())
    response = client.get("/contract-test-response")
    assert response.status_code == 500
    assert response.json()["code"] == "RESPONSE_CONTRACT_ERROR"
    assert "not-public" not in response.text and "secret-invalid-status" not in response.text


def test_response_model_strips_private_fields(client, app):
    @app.get("/contract-test-filter", response_model=Health)
    def filtered():
        return {"status": "ok", "mode": "DEMO", "instance_id": "test", "private_key": "not-public"}
    app.router.routes.insert(0, app.router.routes.pop())
    assert client.get("/contract-test-filter").json() == {"schema_version": "1", "status": "ok", "mode": "DEMO", "instance_id": "test"}


def test_unexpected_exception_has_safe_envelope(app):
    @app.get("/contract-test-unexpected")
    def fail():
        raise RuntimeError("secret-provider-credential")
    app.router.routes.insert(0, app.router.routes.pop())
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/contract-test-unexpected")
    assert response.status_code == 500
    assert response.json()["code"] == "INTERNAL_ERROR"
    assert response.json()["request_id"] == response.headers["X-Request-ID"]
    assert "secret-provider-credential" not in response.text


def test_exact_loopback_origin_on_isolated_port(client):
    client.base_url = "http://127.0.0.1:43219"
    login = {"username": "owner", "password": "local-demo-owner"}
    assert client.post(P + "/auth/login", json=login, headers={"Origin": str(client.base_url).rstrip('/')}).status_code == 200
    for origin in ["http://127.0.0.1:43220", "https://evil.example", "http://127.0.0.1.evil.example:43219", "null"]:
        response = client.post(P + "/auth/login", json=login, headers={"Origin": origin})
        assert response.status_code == 403
        assert response.json()["code"] == "ORIGIN_NOT_ALLOWED"


def test_approval_conflicts_have_actionable_codes(owner):
    response = owner.post(P + "/proposals", json={"instrument_id": "DEMO_NOVA", "side": "BUY", "quantity": 1})
    proposal = response.json()
    response = owner.post(P + f"/proposals/{proposal['id']}/approve", json={"digest": "0" * 64})
    assert response.json()["code"] == "APPROVAL_HASH_MISMATCH"
    owner.post(P + "/accounts/kill-switch", json={"enabled": True})
    response = owner.post(P + "/proposals", json={"instrument_id": "DEMO_NOVA", "side": "BUY", "quantity": 1})
    assert response.json()["code"] == "EXECUTION_PAUSED"
