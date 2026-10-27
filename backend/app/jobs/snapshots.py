"""Capture work inputs at submission, not at an arbitrary later worker time."""
import copy
import hashlib
import json
from datetime import datetime
from sqlalchemy import select
from app.core.errors import ApiError
from app.core.security import iso_now
from app.db.models import Instrument, Strategy, Event
from app.marketdata.demo import DATASET_VERSION


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def freeze_input(db, kind, request):
    refs = dict(request)
    if kind == "backtest":
        strategy = db.get(Strategy, request["strategy_version_id"])
        if strategy is None:
            raise ApiError(404, "STRATEGY_NOT_FOUND", "Strategy version not found")
        instrument = db.get(Instrument, strategy.spec["instrument_id"])
        payload = {"kind": kind, "dataset": DATASET_VERSION, "strategy_version_id": strategy.id, "strategy": strategy.spec, "instrument": {"id": instrument.id, "name": instrument.name}, "bars": instrument.bars}
        refs["instrument_id"] = instrument.id
    elif kind == "research":
        instrument = db.get(Instrument, request["instrument_id"])
        if instrument is None:
            raise ApiError(404, "INSTRUMENT_NOT_FOUND", "Instrument not found")
        cutoff = request.get("as_of")
        if cutoff is None:
            cutoff = instrument.bars[-1]["time"]
        events = [{**e.payload, "id": e.id, "title": e.title, "domain": e.domain, "available_at": e.available_at} for e in db.scalars(select(Event).order_by(Event.available_at, Event.id)) if instrument.id in e.payload["instrument_ids"] and datetime.fromisoformat(e.available_at).timestamp() <= cutoff]
        payload = {"kind": kind, "instrument": {"id": instrument.id, "name": instrument.name}, "events": events, "as_of": cutoff}
        refs["as_of"] = cutoff
    else:
        raise ApiError(422, "UNSUPPORTED_JOB", "Unsupported job type")
    snapshot = copy.deepcopy(payload)
    return {**refs, "snapshot_version": "1", "snapshot_hash": canonical_hash(snapshot), "captured_at": iso_now(), "_snapshot": snapshot}


def verified_snapshot(job):
    if job.input.get("snapshot_version") != "1" or "_snapshot" not in job.input:
        raise ValueError("Legacy queued job has no frozen input. Submit a new run.")
    snapshot = job.input["_snapshot"]
    if not isinstance(snapshot, dict) or canonical_hash(snapshot) != job.input.get("snapshot_hash") or snapshot.get("kind") != job.kind:
        raise ValueError("Frozen input integrity check failed.")
    return snapshot
