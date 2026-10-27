from datetime import datetime, timezone

import pytest
from conftest import sign_in
from app.gathering import service

P = "/api/v1/gathering"
T1 = datetime(2026, 10, 27, 10, tzinfo=timezone.utc)
T2 = datetime(2026, 10, 27, 11, tzinfo=timezone.utc)


def imported(owner, **changes):
    data = {"idempotency_key": "history-first-001", "publisher": "Test publisher",
            "url": "https://example.com/old-release", "title": "Earlier policy announcement",
            "text": "An archived source description with a documented policy change.",
            "domain_ids": ["macroeconomics"], "published_at": "2024-09-18T18:00:00Z",
            "note": "Offline test source, not a genuine publication."}
    data.update(changes)
    return owner.post(P + "/imports", json=data)


def test_seed_configuration_is_inert_and_named_for_user(owner):
    config = owner.get(P + "/config").json()
    assert {d["name"] for d in config["domains"]} == {"Nvidia", "Amazon", "Macroeconomics", "Geopolitics"}
    assert config["settings"]["enabled"] is False
    assert config["network_allowed"] is False
    assert config["sources"] == []
    assert config["can_manage"] is True
    assert {c["key"] for c in config["catalog"]} >= {"nvidia-news", "aws-news", "fed-monetary", "ecb-press", "eu-council"}
    assert owner.get(P + "/documents").json()["total"] == 0


def test_shared_reads_and_owner_only_writes(owner):
    assert imported(owner).status_code == 201
    sign_in(owner, "partner")
    assert owner.get(P + "/config").json()["can_manage"] is False
    assert owner.get(P + "/documents").json()["total"] == 1
    assert imported(owner, idempotency_key="partner-attempt").status_code == 403
    assert owner.put(P + "/settings", json={"expected_revision": 1, "enabled": True}).status_code == 403
    assert owner.post(P + "/domains", json={"name": "Other topic"}).status_code == 403


def test_gathering_requires_login_and_csrf(client):
    assert client.get(P + "/config").status_code == 401
    sign_in(client)
    client.headers.pop("X-CSRF-Token")
    assert client.post(P + "/domains", json={"name": "Other topic"}).status_code == 403


def test_domain_edits_have_versions_and_unique_names(owner):
    created = owner.post(P + "/domains", json={"name": " Energy ", "keywords": [" oil ", "gas", "oil"]})
    assert created.status_code == 201
    row = created.json()
    assert row["name"] == "Energy" and row["keywords"] == ["oil", "gas"]
    assert owner.post(P + "/domains", json={"name": "ENERGY"}).status_code == 409
    update = {"expected_revision": 1, "name": "Energy supply", "keywords": ["oil"], "enabled": False}
    saved = owner.put(P + f"/domains/{row['id']}", json=update)
    assert saved.status_code == 200 and saved.json()["revision"] == 2
    assert owner.put(P + f"/domains/{row['id']}", json=update).status_code == 409


def test_source_configuration_restricts_catalog_and_domains(owner):
    data = {"catalog_key": "fed-monetary", "domain_ids": ["macroeconomics"], "interval_minutes": 60}
    assert owner.post(P + "/sources", json={**data, "catalog_key": "https://127.0.0.1/private"}).status_code == 422
    assert owner.post(P + "/sources", json={**data, "domain_ids": ["missing"]}).status_code == 422
    assert owner.post(P + "/sources", json={**data, "interval_minutes": 1}).status_code == 422
    created = owner.post(P + "/sources", json=data)
    assert created.status_code == 201
    assert owner.post(P + "/sources", json=data).status_code == 409
    source = created.json()
    edit = {"expected_revision": 1, "domain_ids": ["macroeconomics", "geopolitics"], "enabled": True, "interval_minutes": 120}
    assert owner.put(P + f"/sources/{source['id']}", json=edit).json()["revision"] == 2
    assert owner.put(P + f"/sources/{source['id']}", json=edit).status_code == 409
    # Database activation cannot bypass the process-level test network prohibition.
    assert owner.put(P + "/settings", json={"expected_revision": 1, "enabled": True}).status_code == 200
    assert owner.post(P + f"/sources/{source['id']}/collect").status_code == 409
    assert owner.get(P + "/runs").json() == []


def test_backfill_never_claims_prior_app_knowledge(owner, monkeypatch):
    monkeypatch.setattr(service, "utcnow", lambda: T1)
    response = imported(owner)
    assert response.status_code == 201, response.text
    doc_id = response.json()["document_id"]
    detail = owner.get(P + f"/documents/{doc_id}").json()
    doc = detail["document"]
    assert doc["source_kind"] == "MANUAL"
    assert doc["first_seen_at"] == T1.isoformat()
    assert doc["revision"]["published_at"].startswith("2024-09-18")
    assert doc["revision"]["available_at"] == T1.isoformat()
    assert owner.get(P + "/documents", params={"known_by": "2026-10-27T09:59:59Z"}).json()["total"] == 0
    assert owner.get(P + f"/documents/{doc_id}", params={"known_by": "2024-10-01T00:00:00Z"}).status_code == 404


def test_idempotent_import_and_append_only_corrections(owner, monkeypatch):
    monkeypatch.setattr(service, "utcnow", lambda: T1)
    first = imported(owner).json()
    assert imported(owner).json() == first
    assert imported(owner, text="Changed content under an already-used request key.").status_code == 409
    unchanged = imported(owner, idempotency_key="history-repeat-002").json()
    assert unchanged == {**first, "created": False, "changed": False}
    monkeypatch.setattr(service, "utcnow", lambda: T2)
    corrected = imported(owner, idempotency_key="history-correct-003", title="Corrected policy announcement",
                         text="A corrected policy account with a new emphasis.", domain_ids=["geopolitics"]).json()
    assert corrected["document_id"] == first["document_id"] and corrected["revision"] == 2
    history = owner.get(P + f"/documents/{first['document_id']}").json()
    assert [r["revision"] for r in history["revisions"]] == [2, 1]
    assert history["revisions"][1]["title"] == "Earlier policy announcement"
    cutoff = owner.get(P + f"/documents/{first['document_id']}", params={"known_by": T1.isoformat()}).json()
    assert len(cutoff["revisions"]) == 1 and cutoff["document"]["revision"]["revision"] == 1
    # Apply filters after choosing the newest eligible revision.
    assert owner.get(P + "/documents", params={"domain_id": "macroeconomics"}).json()["total"] == 0
    assert owner.get(P + "/documents", params={"q": "Earlier"}).json()["total"] == 0
    assert owner.get(P + "/documents", params={"domain_id": "macroeconomics", "known_by": T1.isoformat()}).json()["total"] == 1


def test_reversion_is_a_new_revision_and_domain_edits_do_not_rewrite_history(owner, monkeypatch):
    monkeypatch.setattr(service, "utcnow", lambda: T1)
    first = imported(owner).json()
    imported(owner, idempotency_key="revision-two-002", text="A new source interpretation for revision two.")
    third = imported(owner, idempotency_key="revision-three-003").json()
    assert third["revision"] == 3
    owner.put(P + "/domains/macroeconomics", json={"expected_revision": 1, "name": "Macro renamed", "keywords": ["new"]})
    detail = owner.get(P + f"/documents/{first['document_id']}").json()
    assert detail["document"]["revision"]["domains"][0]["name"] == "Macroeconomics"


@pytest.mark.parametrize("changes", [
    {"url": "javascript:alert(1)"}, {"url": "https://user:secret@example.com/path"},
    {"domain_ids": []}, {"published_at": "2024-01-01T00:00:00"}, {"text": "short"},
])
def test_invalid_import_is_rejected(owner, changes):
    assert imported(owner, **changes).status_code == 422
    assert owner.get(P + "/documents").json()["total"] == 0


def test_filters_pagination_unknown_dates_and_export_history(owner):
    first = imported(owner).json()
    imported(owner, idempotency_key="another-source-002", url="https://example.com/second", published_at=None)
    page = owner.get(P + "/documents", params={"limit": 1}).json()
    assert page["total"] == 2 and len(page["items"]) == 1
    next_page = owner.get(P + "/documents", params={"limit": 1, "offset": 1}).json()
    assert next_page["items"][0]["id"] != page["items"][0]["id"]
    by_date = owner.get(P + "/documents", params={"date_from": "2024-01-01T00:00:00Z", "date_to": "2024-12-31T23:59:59Z"}).json()
    assert by_date["total"] == 1 and by_date["items"][0]["id"] == first["document_id"]
    assert owner.get(P + "/documents", params={"q": "%"}).json()["total"] == 0
    assert owner.get(P + "/documents", params={"known_by": "2024-01-01"}).status_code == 422
    assert owner.get(P + "/documents", params={"date_from": "2025-01-01T00:00:00Z", "date_to": "2024-01-01T00:00:00Z"}).status_code == 422
    assert owner.get(P + "/documents", params={"limit": 101}).status_code == 422


def test_future_publication_is_visible_but_not_eligible_for_prior_cutoff(owner, monkeypatch):
    monkeypatch.setattr(service, "utcnow", lambda: T1)
    imported(owner, published_at="2027-01-01T00:00:00Z")
    assert owner.get(P + "/documents").json()["total"] == 1
    assert owner.get(P + "/documents", params={"known_by": T2.isoformat()}).json()["total"] == 0


def test_guide_served_without_external_resources(client):
    response = client.get("/help/user-guide.html")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "default-src 'none'" in response.headers["content-security-policy"]
    assert response.headers["x-frame-options"] == "SAMEORIGIN"
    assert "<script" not in response.text.lower()
    assert "Gathering" in response.text or "gathering" in response.text


def test_curated_bulk_import_is_validated_before_writes_and_retry_safe(owner, app, tmp_path, monkeypatch):
    import json
    from pathlib import Path
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    from import_research import import_file
    starter = Path(__file__).resolve().parents[2] / "data/research/starter-backfill.json"
    payload = json.loads(starter.read_text(encoding="utf-8"))
    invalid = tmp_path / "invalid.json"
    invalid.write_text(json.dumps([payload[0], {"title": "Incomplete second record"}]))
    with pytest.raises(ValueError):
        import_file(invalid, app.state.sessions)
    assert owner.get(P + "/documents").json()["total"] == 0
    first = import_file(starter, app.state.sessions)
    assert len(first) == 4 and all(row["created"] for row in first)
    assert import_file(starter, app.state.sessions) == first
    records = owner.get(P + "/documents").json()
    assert records["total"] == 4
    assert sum(row["revision"]["published_on"] is not None for row in records["items"]) == 3
