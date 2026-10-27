from concurrent.futures import ThreadPoolExecutor
from sqlalchemy import select, update
from app.db.models import Job, Notification
from app.agents.research import run_research
from app.quant.backtest import VectorbtResearchAdapter
from app.jobs.snapshots import verified_snapshot


class LocalJobRunner:
    """One local worker; persisted inputs/results. Interrupted work is not claimed complete."""
    def __init__(self, sessions):
        self.sessions = sessions
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="aitrader-quant")

    def recover(self):
        with self.sessions() as db:
            for job in db.scalars(select(Job).where(Job.status == "RUNNING")):
                job.status, job.error = "FAILED", "Interrupted by a server restart. Start a new run."
            pending = list(db.scalars(select(Job.id).where(Job.status == "PENDING")))
            db.commit()
        for jid in pending:
            self.submit(jid)

    def submit(self, jid):
        self.pool.submit(self.run, jid)

    def run(self, jid):
        with self.sessions() as db:
            claimed = db.execute(update(Job).where(Job.id == jid, Job.status == "PENDING").values(status="RUNNING"))
            if claimed.rowcount != 1:
                db.rollback()
                return
            db.commit()
            job = db.get(Job, jid)
            try:
                snapshot = verified_snapshot(job)
                if job.kind == "backtest":
                    result = VectorbtResearchAdapter().run(snapshot["bars"], snapshot["strategy"])
                    result["strategy_version_id"] = snapshot["strategy_version_id"]
                else:
                    result = run_research(snapshot["instrument"], snapshot["events"])
                    result["as_of"] = snapshot["as_of"]
                    db.add(Notification(id=f"notice-{jid}", user_id=job.user_id, message=f"Research for {snapshot['instrument']['name']} is ready. {len(snapshot['events'])} fictional event(s) reviewed."))
                result["input_hash"] = job.input["snapshot_hash"]
                job.result, job.status = result, "SUCCEEDED"
            except Exception as exc:
                # Never return provider exception text or credentials to the browser.
                job.status, job.error = "FAILED", f"{type(exc).__name__}: calculation failed; no substitute result was generated."
                import logging
                logging.getLogger("aitrader.jobs").exception("Local calculation failed: %s", jid)
            db.commit()

    def close(self):
        self.pool.shutdown(wait=True)
