"""Inactive interests stop new coverage without rewriting historical evidence."""
from datetime import datetime, timezone

import pytest

from app.core.errors import ApiError
from app.db.models import GatheringRun, GatheringSource
from app.gathering import service
from app.gathering.contracts import (GatheringDomainUpdate, GatheringSettingsUpdate,
    GatheringSourceCreate, GatheringManualImport)


def _domain(db, did, enabled):
    domain = next(d for d in service.get_config(db, "owner")["domains"] if d["id"] == did)
    return service.save_domain(db, "owner", GatheringDomainUpdate(
        expected_revision=domain["revision"], name=domain["name"], description=domain["description"],
        keywords=domain["keywords"], enabled=enabled), did)


def _configured(app, monkeypatch):
    monkeypatch.setattr(service.settings, "public_feed_requests_allowed", True)
    with app.state.sessions() as db:
        service.update_settings(db, "owner", GatheringSettingsUpdate(expected_revision=1, enabled=True))
        return service.save_source(db, "owner", GatheringSourceCreate(
            catalog_key="fed-monetary", domain_ids=["nvidia", "macroeconomics"], enabled=True))


def test_only_active_domains_enter_new_run_but_assignments_are_retained(client, app, monkeypatch):
    source = _configured(app, monkeypatch)
    with app.state.sessions() as db:
        _domain(db, "nvidia", False)
        queued = service.queue_collection(db, "owner", source["id"])
        assert [domain["id"] for domain in queued["snapshot"]["domains"]] == ["macroeconomics"]
        assert db.get(GatheringSource, source["id"]).domain_ids == ["nvidia", "macroeconomics"]
        assert service.claim_collection(db, queued["id"])
        service.finish_collection(db, queued["id"], [{"external_id": "1", "url": "https://example.org/source", "title": "Stored publisher statement", "summary": "This original source remains available after domain changes.", "published_at": None, "updated_at": None}], datetime.now(timezone.utc).isoformat())
        document = service.list_documents(db)["items"][0]
        _domain(db, "macroeconomics", False)
        # Existing coverage and source content remain intact after pausing interest.
        assert service.get_document(db, document["id"])["document"]["revision"]["domain_ids"] == ["macroeconomics"]
        assert service.get_config(db, "owner")["settings"]["enabled"] is True
        assert db.get(GatheringSource, source["id"]).enabled is True
        assert service.queue_due(db) == []
        with pytest.raises(ApiError) as error:
            service.queue_collection(db, "owner", source["id"])
        assert error.value.code == "COLLECTION_DISABLED"


def test_all_domains_inactive_cancel_queued_claim_and_can_resume(client, app, monkeypatch):
    source = _configured(app, monkeypatch)
    with app.state.sessions() as db:
        queued = service.queue_collection(db, "owner", source["id"])
        _domain(db, "nvidia", False)
        _domain(db, "macroeconomics", False)
        assert service.claim_collection(db, queued["id"]) is None
        assert db.get(GatheringRun, queued["id"]).status == "CANCELLED"
        assert db.get(GatheringSource, source["id"]).active_run_id is None
        assert service.queue_due(db) == []
        _domain(db, "nvidia", True)
        resumed = service.queue_collection(db, "owner", source["id"])
        assert [domain["id"] for domain in resumed["snapshot"]["domains"]] == ["nvidia"]
        # First queued scope is frozen even after cancellation and later settings.
        assert [domain["id"] for domain in db.get(GatheringRun, queued["id"]).snapshot["domains"]] == ["nvidia", "macroeconomics"]


def test_manual_history_can_explicitly_reference_inactive_domain(client, app):
    with app.state.sessions() as db:
        _domain(db, "amazon", False)
        result = service.import_document(db, "owner", GatheringManualImport(
            idempotency_key="inactive-domain-import", publisher="Historical publisher", url="https://example.org/archive",
            title="Archived source statement", text="Historical material kept for later comparison.", domain_ids=["amazon"],
            published_at="2020-01-01T00:00:00Z"))
        document = service.get_document(db, result["document_id"])["document"]
        assert document["revision"]["domain_ids"] == ["amazon"]
        assert document["revision"]["domains"][0]["enabled"] is False
        assert service.get_config(db, "owner")["settings"]["enabled"] is False
