"""Bounded public-feed collection in the single local application process."""
import logging
from concurrent.futures import ThreadPoolExecutor
from threading import Event, Lock, Thread
from sqlalchemy import select

from app.core.config import settings
from app.db.models import GatheringRun
from app.gathering.catalog import CATALOG
from app.gathering.feeds import FeedError, fetch_feed
from app.gathering.service import (
    claim_collection, fail_collection, finish_collection, queue_due,
    recover_collections,
)

logger = logging.getLogger("aitrader.gathering")


class GatheringRunner:
    """One fetch at a time; SQL claims remain authoritative across duplicate work."""

    def __init__(self, sessions, fetcher=None, poll_seconds=15):
        self.sessions = sessions
        self.fetcher = fetcher or fetch_feed
        self.poll_seconds = poll_seconds
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="aitrader-feeds")
        self.stopping = Event()
        self.lock = Lock()
        self.submitted = set()
        self.pending_finalizations = {}
        self.thread = None

    def start(self):
        with self.sessions() as db:
            pending = recover_collections(db)
        for run_id in pending:
            self.submit(run_id)
        if settings.public_feed_requests_allowed:
            self.thread = Thread(target=self._schedule, name="aitrader-feed-schedule", daemon=True)
            self.thread.start()

    def _schedule(self):
        while not self.stopping.is_set():
            try:
                self.tick()
            except Exception:
                # Provider/SQL exception strings may include input data. Keep the
                # recurring scheduler healthy without logging those strings.
                logger.warning("Feed scheduler could not check due sources; it will retry.")
            self.stopping.wait(self.poll_seconds)

    def tick(self):
        if self.stopping.is_set():
            return
        self._retry_finalizations()
        if not settings.public_feed_requests_allowed:
            return
        with self.sessions() as db:
            pending = queue_due(db)
            # A transient claim failure must not strand QUEUED work until restart.
            pending += list(db.scalars(select(GatheringRun.id).where(GatheringRun.status == "QUEUED")))
        for run_id in pending:
            self.submit(run_id)

    def submit(self, run_id):
        with self.lock:
            if self.stopping.is_set() or run_id in self.submitted:
                return
            self.submitted.add(run_id)
            try:
                future = self.pool.submit(self.run, run_id)
            except RuntimeError:
                self.submitted.discard(run_id)
                return
        future.add_done_callback(lambda _: self._finished(run_id))

    def _finished(self, run_id):
        with self.lock:
            self.submitted.discard(run_id)

    def _record_failure(self, run_id, code):
        try:
            with self.sessions() as db:
                fail_collection(db, run_id, code)
        except Exception:
            # The network attempt is over. Retain only a status-write retry;
            # fetching again could duplicate work or lose the original failure.
            with self.lock:
                self.pending_finalizations[run_id] = code
            logger.warning("Feed outcome could not be stored; its status will be retried.")
        else:
            with self.lock:
                self.pending_finalizations.pop(run_id, None)

    def _retry_finalizations(self):
        with self.lock:
            pending = [(run_id, code) for run_id, code in self.pending_finalizations.items()
                       if run_id not in self.submitted]
        for run_id, code in pending:
            self._record_failure(run_id, code)

    def run(self, run_id):
        if self.stopping.is_set():
            return  # Persisted queued work can resume on the next server start.
        with self.sessions() as db:
            snapshot = claim_collection(db, run_id)
        if snapshot is None:
            return
        try:
            if self.stopping.is_set():
                self._record_failure(run_id, "COLLECTION_DISABLED")
                return
            catalog = CATALOG.get(snapshot["catalog_key"])
            if not catalog or catalog["url"] != snapshot["url"]:
                self._record_failure(run_id, "CATALOG_CHANGED")
                return
            # No database transaction is kept open during the HTTP request.
            result = self.fetcher(snapshot["catalog_key"])
            metadata = {key: result[key] for key in (
                "http_status", "content_sha256", "skipped_items", "truncated"
            ) if key in result}
            with self.sessions() as db:
                finish_collection(db, run_id, result["items"], result["fetched_at"], metadata=metadata)
        except FeedError as error:
            self._record_failure(run_id, error.code)
        except Exception:
            self._record_failure(run_id, "COLLECTION_FAILED")

    def close(self):
        self.stopping.set()
        if self.thread:
            self.thread.join(timeout=3)
        self.pool.shutdown(wait=True)
        self._retry_finalizations()
