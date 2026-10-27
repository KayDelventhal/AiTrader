from datetime import datetime, timezone

from sqlalchemy import select

from app.db.models import ResearchDocumentRevision
from app.gathering import service


def _source(**extra):
    return {"idempotency_key": "date-only-source", "publisher": "Historical publisher",
            "url": "https://example.org/2024/publication", "title": "A dated historical publication",
            "text": "A source excerpt whose publisher establishes a calendar date only.",
            "domain_ids": ["nvidia"], "published_on": "2024-03-18", **extra}


def test_date_only_import_filters_without_inventing_timestamp(owner, monkeypatch):
    now = datetime(2026, 10, 27, 12, tzinfo=timezone.utc)
    monkeypatch.setattr(service, "utcnow", lambda: now)
    response = owner.post("/api/v1/gathering/imports", json=_source())
    assert response.status_code == 201, response.text
    did = response.json()["document_id"]
    document = owner.get(f"/api/v1/gathering/documents/{did}").json()["document"]
    revision = document["revision"]
    assert revision["published_at"] is None
    assert revision["published_on"] == "2024-03-18"
    assert document["first_seen_at"] == revision["recorded_at"] == revision["available_at"] == now.isoformat()
    assert owner.get("/api/v1/gathering/documents", params={"known_by": "2024-03-19T00:00:00Z"}).json()["total"] == 0
    # A date-only claim can match that calendar day, not an invented time within it.
    on_day = owner.get("/api/v1/gathering/documents", params={"date_from": "2024-03-18T12:00:00Z", "date_to": "2024-03-18T13:00:00Z"}).json()
    assert on_day["total"] == 1
    assert owner.get("/api/v1/gathering/documents", params={"date_from": "2024-03-19T00:00:00Z"}).json()["total"] == 0
    assert owner.get("/api/v1/gathering/documents", params={"date_to": "2024-03-17T23:59:59Z"}).json()["total"] == 0


def test_date_only_and_exact_publications_share_calendar_order(owner):
    assert owner.post("/api/v1/gathering/imports", json=_source()).status_code == 201
    assert owner.post("/api/v1/gathering/imports", json=_source(idempotency_key="later-exact-source",
        url="https://example.org/later", published_on=None, published_at="2024-03-19T09:00:00Z", title="Later exact publication")).status_code == 201
    assert owner.post("/api/v1/gathering/imports", json=_source(idempotency_key="earlier-date-source",
        url="https://example.org/earlier", published_on="2024-03-17", title="Earlier dated publication")).status_code == 201
    titles = [item["revision"]["title"] for item in owner.get("/api/v1/gathering/documents").json()["items"]]
    assert titles == ["Later exact publication", "A dated historical publication", "Earlier dated publication"]


def test_date_precision_conflict_and_future_historical_date_rejected(owner):
    assert owner.post("/api/v1/gathering/imports", json=_source(published_at="2024-03-18T12:00:00Z")).status_code == 422
    assert owner.post("/api/v1/gathering/imports", json=_source(published_on="2099-01-01")).status_code == 422
    assert owner.get("/api/v1/gathering/documents").json()["total"] == 0


def test_legacy_revision_without_date_only_field_remains_readable_and_dedupes(owner, app):
    payload = _source(published_on=None, published_at="2024-03-18T12:00:00Z")
    created = owner.post("/api/v1/gathering/imports", json=payload).json()
    with app.state.sessions() as db:
        row = db.scalar(select(ResearchDocumentRevision).where(ResearchDocumentRevision.document_id == created["document_id"]))
        old = dict(row.payload)
        old.pop("published_on")
        row.payload = old
        db.commit()
    detail = owner.get(f"/api/v1/gathering/documents/{created['document_id']}")
    assert detail.status_code == 200
    assert detail.json()["document"]["revision"]["published_on"] is None
    repeat = owner.post("/api/v1/gathering/imports", json={**payload, "idempotency_key": "repeat-legacy-import"})
    assert repeat.status_code == 201
    assert repeat.json()["changed"] is False
    assert repeat.json()["revision"] == 1
