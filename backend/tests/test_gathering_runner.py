from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from threading import Event

import pytest
from sqlalchemy import select

from app.core.config import settings
from app.db.models import GatheringRun, GatheringSource, GatheringSettings
from app.gathering import service
from app.gathering.catalog import CATALOG
from app.gathering.contracts import GatheringSourceCreate, GatheringSettingsUpdate
from app.gathering.feeds import FeedError
from app.gathering.runner import GatheringRunner
import app.gathering.runner as runner_module

NOW = datetime(2026, 10, 27, 12, tzinfo=timezone.utc)


@pytest.fixture
def configured(owner, app, monkeypatch):
    app.state.gathering.close()
    monkeypatch.setattr(settings, "public_feed_requests_allowed", True)
    monkeypatch.setattr(service, "utcnow", lambda: NOW)
    with app.state.sessions() as db:
        service.update_settings(db, "owner", GatheringSettingsUpdate(expected_revision=1, enabled=True))
        source = service.save_source(db, "owner", GatheringSourceCreate(
            catalog_key="fed-monetary", domain_ids=["macroeconomics"], enabled=True, interval_minutes=60))
    return app.state.sessions, source


def queued(sessions, source):
    with sessions() as db:
        return service.queue_collection(db, "owner", source["id"])


def fetched(content="A publisher-provided excerpt."):
    return {"items": [{"external_id": "release-001", "url": "https://example.com/policy",
                       "title": "Policy release", "summary": content,
                       "published_at": "2024-09-18T18:00:00+00:00", "updated_at": None}],
            "fetched_at": NOW.isoformat(), "http_status": 200, "content_sha256": "a" * 64,
            "skipped_items": 0, "truncated": False}


def run_state(sessions, rid):
    with sessions() as db:
        return service.run_view(db.get(GatheringRun, rid))


def test_runner_claim_is_idempotent_and_stores_provenance(configured):
    sessions, source = configured
    calls = []
    worker = GatheringRunner(sessions, lambda key: calls.append(key) or fetched())
    try:
        run = queued(sessions, source)
        worker.run(run["id"])
        worker.run(run["id"])
        state = run_state(sessions, run["id"])
        assert state["status"] == "SUCCEEDED" and calls == ["fed-monetary"]
        assert state["counts"] == {"received": 1, "new_documents": 1, "new_revisions": 0, "unchanged": 0}
        assert state["metadata"]["model_calls"] == 0
        with sessions() as db:
            page = service.list_documents(db)
            revision = page["items"][0]["revision"]
            assert revision["recorded_at"] == NOW.isoformat()
            assert revision["published_at"].startswith("2024-09-18")
            assert revision["original"]["external_id"] == "release-001"
            assert "relevance has not been reviewed" in revision["attribution"]
            assert db.get(GatheringSource, source["id"]).active_run_id is None
    finally:
        worker.close()


def test_duplicate_queue_requests_and_concurrent_claims(configured):
    sessions, source = configured
    with ThreadPoolExecutor(max_workers=5) as pool:
        ids = list(pool.map(lambda _: queued(sessions, source)["id"], range(5)))
    assert len(set(ids)) == 1
    calls = []
    worker = GatheringRunner(sessions, lambda key: calls.append(key) or fetched())
    try:
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(worker.run, ids[:4]))
        assert calls == ["fed-monetary"]
        assert run_state(sessions, ids[0])["status"] == "SUCCEEDED"
    finally:
        worker.close()


def test_scheduler_coalesces_missed_intervals(configured):
    sessions, source = configured
    with sessions() as db:
        db.get(GatheringSource, source["id"]).next_due_at = (NOW - timedelta(days=100)).isoformat()
        db.commit()
        first = service.queue_due(db)
        assert len(first) == 1
        assert service.queue_due(db) == []
        assert db.get(GatheringSource, source["id"]).next_due_at == (NOW + timedelta(hours=1)).isoformat()
        service.fail_collection(db, first[0])
        assert service.queue_due(db) == []


@pytest.mark.parametrize("gate", ["workspace", "source", "process"])
def test_disable_before_claim_prevents_fetch(configured, monkeypatch, gate):
    sessions, source = configured
    run = queued(sessions, source)
    with sessions() as db:
        if gate == "workspace":
            db.get(GatheringSettings, 1).enabled = False
        elif gate == "source":
            db.get(GatheringSource, source["id"]).enabled = False
        else:
            monkeypatch.setattr(settings, "public_feed_requests_allowed", False)
        db.commit()
    worker = GatheringRunner(sessions, lambda key: pytest.fail("Disabled collection must not fetch"))
    try:
        worker.run(run["id"])
        assert run_state(sessions, run["id"])["status"] == "CANCELLED"
    finally:
        worker.close()


def test_catalog_change_does_not_retarget_frozen_request(configured, monkeypatch):
    sessions, source = configured
    run = queued(sessions, source)
    monkeypatch.setitem(CATALOG, "fed-monetary", {**CATALOG["fed-monetary"], "url": "https://example.com/new-feed"})
    worker = GatheringRunner(sessions, lambda key: pytest.fail("Changed catalog URL must not be fetched"))
    try:
        worker.run(run["id"])
        state = run_state(sessions, run["id"])
        assert state["status"] == "FAILED" and "endpoint changed" in state["error"]
    finally:
        worker.close()


@pytest.mark.parametrize("error", [FeedError("INVALID_FEED", "unsafe provider text"), RuntimeError("secret-password-in-url")])
def test_failed_fetch_redacts_error_and_never_invents_data(configured, error):
    sessions, source = configured
    def fail(_):
        raise error
    worker = GatheringRunner(sessions, fail)
    try:
        run = queued(sessions, source)
        worker.run(run["id"])
        state = run_state(sessions, run["id"])
        assert state["status"] == "FAILED"
        assert "unsafe" not in state["error"] and "password" not in state["error"]
        with sessions() as db:
            assert service.list_documents(db)["total"] == 0
            assert db.get(GatheringSource, source["id"]).last_success_at is None
    finally:
        worker.close()


def test_restart_marks_interrupted_fetch_failed_and_releases_source(configured):
    sessions, source = configured
    run = queued(sessions, source)
    with sessions() as db:
        assert service.claim_collection(db, run["id"])
        assert service.recover_collections(db) == []
        assert db.get(GatheringRun, run["id"]).status == "FAILED"
        assert db.get(GatheringSource, source["id"]).active_run_id is None
        assert service.queue_due(db) == []


def test_restart_returns_queued_work_and_cancels_if_disabled(configured):
    sessions, source = configured
    run = queued(sessions, source)
    with sessions() as db:
        assert service.recover_collections(db) == [run["id"]]
        db.get(GatheringSettings, 1).enabled = False
        db.commit()
        assert service.recover_collections(db) == []
        assert db.get(GatheringRun, run["id"]).status == "CANCELLED"


def test_repeated_collection_retains_history_and_honors_cooldown(configured, monkeypatch):
    sessions, source = configured
    with sessions() as db:
        r1 = service.queue_collection(db, "owner", source["id"])
        service.claim_collection(db, r1["id"])
        service.finish_collection(db, r1["id"], fetched()["items"], NOW.isoformat())
        with pytest.raises(Exception) as raised:
            service.queue_collection(db, "owner", source["id"])
        assert getattr(raised.value, "status_code", None) == 429
    monkeypatch.setattr(service, "utcnow", lambda: NOW + timedelta(minutes=2))
    with sessions() as db:
        r2 = service.queue_collection(db, "owner", source["id"])
        service.claim_collection(db, r2["id"])
        repeated = service.finish_collection(db, r2["id"], fetched()["items"], NOW.isoformat())
        assert repeated["counts"]["unchanged"] == 1
    monkeypatch.setattr(service, "utcnow", lambda: NOW + timedelta(minutes=4))
    with sessions() as db:
        r3 = service.queue_collection(db, "owner", source["id"])
        service.claim_collection(db, r3["id"])
        corrected = service.finish_collection(db, r3["id"], fetched("A corrected publisher excerpt.")["items"], NOW.isoformat())
        assert corrected["counts"]["new_revisions"] == 1
        doc = service.list_documents(db)["items"][0]
        assert len(service.get_document(db, doc["id"])["revisions"]) == 2
        assert service.get_document(db, doc["id"], NOW.isoformat())["document"]["revision"]["content"] == "A publisher-provided excerpt."


def test_config_can_change_while_network_is_waiting(configured):
    sessions, source = configured
    entered, release = Event(), Event()
    def fetch(_):
        entered.set()
        assert release.wait(5)
        return fetched()
    worker = GatheringRunner(sessions, fetch)
    try:
        run = queued(sessions, source)
        worker.submit(run["id"])
        assert entered.wait(3)
        with sessions() as db:
            # This update would block if the fetch held SQLite's write lock.
            service.update_settings(db, "owner", GatheringSettingsUpdate(expected_revision=2, enabled=False))
        release.set()
    finally:
        release.set()
        worker.close()
    assert run_state(sessions, run["id"])["status"] == "SUCCEEDED"


def test_tick_retries_queued_work_after_transient_claim_failure(configured, monkeypatch):
    sessions, source = configured
    original = runner_module.claim_collection
    failed, completed = Event(), Event()
    attempts = []
    def transient(db, rid):
        attempts.append(rid)
        if len(attempts) == 1:
            failed.set()
            raise RuntimeError("Temporary test database contention")
        return original(db, rid)
    monkeypatch.setattr(runner_module, "claim_collection", transient)
    def fetch(_):
        completed.set()
        return fetched()
    worker = GatheringRunner(sessions, fetch)
    try:
        run = queued(sessions, source)
        # Execute directly to reproduce a failed executor attempt deterministically.
        with pytest.raises(RuntimeError):
            worker.run(run["id"])
        assert failed.is_set() and run_state(sessions, run["id"])["status"] == "QUEUED"
        worker.tick()
        assert completed.wait(3)
    finally:
        worker.close()
    assert run_state(sessions, run["id"])["status"] == "SUCCEEDED"


def test_shutdown_does_not_begin_queued_network_work(configured):
    sessions, source = configured
    run = queued(sessions, source)
    worker = GatheringRunner(sessions, lambda _: pytest.fail("Stopped worker fetched"))
    worker.close()
    worker.run(run["id"])
    assert run_state(sessions, run["id"])["status"] == "QUEUED"


def test_terminal_write_retry_waits_for_future_and_never_fetches_again(configured, monkeypatch):
    sessions, source = configured
    calls, failure_attempts = [], []
    allow_fetch, callback_entered, release_callback, finished = Event(), Event(), Event(), Event()
    original_fail = runner_module.fail_collection

    def fetch(key):
        calls.append(key)
        assert allow_fetch.wait(5)
        return fetched()

    def broken_finish(*args, **kwargs):
        raise RuntimeError("Temporary result write failure")

    def transient_failure(db, run_id, code):
        failure_attempts.append(run_id)
        if len(failure_attempts) == 1:
            raise RuntimeError("Temporary terminal write failure")
        return original_fail(db, run_id, code)

    monkeypatch.setattr(runner_module, "finish_collection", broken_finish)
    monkeypatch.setattr(runner_module, "fail_collection", transient_failure)
    worker = GatheringRunner(sessions, fetch)
    original_finished = worker._finished

    def held_callback(run_id):
        callback_entered.set()
        try:
            assert release_callback.wait(5)
        finally:
            original_finished(run_id)
            finished.set()

    monkeypatch.setattr(worker, "_finished", held_callback)
    try:
        run = queued(sessions, source)
        worker.submit(run["id"])
        allow_fetch.set()
        assert callback_entered.wait(3)
        assert run_state(sessions, run["id"])["status"] == "RUNNING"
        worker.tick()
        assert len(failure_attempts) == 1  # Still tracked as submitted work.
        release_callback.set()
        assert finished.wait(3)
        monkeypatch.setattr(settings, "public_feed_requests_allowed", False)
        worker.tick()  # Status recovery does not require network permission.
        assert run_state(sessions, run["id"])["status"] == "FAILED"
        assert calls == ["fed-monetary"] and len(failure_attempts) == 2
        assert worker.pending_finalizations == {}
        with sessions() as db:
            assert db.get(GatheringSource, source["id"]).active_run_id is None
            assert service.list_documents(db)["total"] == 0
    finally:
        allow_fetch.set()
        release_callback.set()
        worker.close()


def test_close_retries_pending_failure_without_another_request(configured, monkeypatch):
    sessions, source = configured
    calls, attempts = [], []
    original_fail = runner_module.fail_collection

    def fetch(key):
        calls.append(key)
        raise FeedError("FEED_TIMEOUT", "Private provider response")

    def transient_failure(db, run_id, code):
        attempts.append(code)
        if len(attempts) == 1:
            raise RuntimeError("Temporary terminal write failure")
        return original_fail(db, run_id, code)

    monkeypatch.setattr(runner_module, "fail_collection", transient_failure)
    worker = GatheringRunner(sessions, fetch)
    try:
        run = queued(sessions, source)
        worker.run(run["id"])
        assert run_state(sessions, run["id"])["status"] == "RUNNING"
        assert worker.pending_finalizations == {run["id"]: "FEED_TIMEOUT"}
    finally:
        worker.close()
    state = run_state(sessions, run["id"])
    assert state["status"] == "FAILED" and state["metadata"]["error_code"] == "FEED_TIMEOUT"
    assert calls == ["fed-monetary"] and attempts == ["FEED_TIMEOUT", "FEED_TIMEOUT"]
    assert worker.pending_finalizations == {}


def test_pending_failure_retry_preserves_already_committed_success(configured, monkeypatch):
    sessions, source = configured
    calls, attempts = [], []
    original_finish, original_fail = runner_module.finish_collection, runner_module.fail_collection

    def committed_finish(*args, **kwargs):
        original_finish(*args, **kwargs)
        raise RuntimeError("Ambiguous acknowledgement after commit")

    def transient_failure(db, run_id, code):
        attempts.append(code)
        if len(attempts) == 1:
            raise RuntimeError("Temporary terminal write failure")
        return original_fail(db, run_id, code)

    monkeypatch.setattr(runner_module, "finish_collection", committed_finish)
    monkeypatch.setattr(runner_module, "fail_collection", transient_failure)
    worker = GatheringRunner(sessions, lambda key: calls.append(key) or fetched())
    try:
        run = queued(sessions, source)
        worker.run(run["id"])
        assert worker.pending_finalizations
        worker.tick()
        assert run_state(sessions, run["id"])["status"] == "SUCCEEDED"
        assert worker.pending_finalizations == {} and calls == ["fed-monetary"]
        with sessions() as db:
            assert service.list_documents(db)["total"] == 1
            assert db.get(GatheringSource, source["id"]).active_run_id is None
    finally:
        worker.close()
