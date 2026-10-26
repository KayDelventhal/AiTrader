from concurrent.futures import ThreadPoolExecutor
from sqlalchemy import select
from app.db.models import Job, Strategy, Instrument, Event, Notification
from app.agents.research import run_research
from app.quant.backtest import VectorbtResearchAdapter
from datetime import datetime, timezone


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
            job = db.get(Job, jid)
            if not job or job.status != "PENDING":
                return
            job.status = "RUNNING"
            db.commit()
            try:
                if job.kind == "backtest":
                    strategy = db.get(Strategy, job.input["strategy_version_id"])
                    instrument = db.get(Instrument, strategy.spec["instrument_id"])
                    result = VectorbtResearchAdapter().run(instrument.bars, strategy.spec)
                    result["strategy_version_id"] = strategy.id
                else:
                    instrument = db.get(Instrument, job.input["instrument_id"])
                    cutoff = job.input.get("as_of") or instrument.bars[-1]["time"]
                    events = [{"id": e.id, "title": e.title, **e.payload} for e in db.scalars(select(Event)) if instrument.id in e.payload["instrument_ids"] and datetime.fromisoformat(e.available_at).timestamp() <= cutoff]
                    result = run_research({"id": instrument.id, "name": instrument.name}, events)
                    result["as_of"] = cutoff
                    db.add(Notification(id=f"notice-{jid}", user_id=job.user_id, message=f"Research for {instrument.name} is ready. {len(events)} fictional event(s) reviewed."))
                job.result, job.status = result, "SUCCEEDED"
            except Exception as exc:
                # Never return provider exception text or credentials to the browser.
                job.status, job.error = "FAILED", f"{type(exc).__name__}: calculation failed; no substitute result was generated."
                import logging
                logging.getLogger("aitrader.jobs").exception("Local calculation failed: %s", jid)
            db.commit()

    def close(self):
        self.pool.shutdown(wait=True)
