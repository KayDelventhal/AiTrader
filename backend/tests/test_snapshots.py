import copy
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import select

from app.db.models import Event, Instrument, Job, Notification, Strategy
from app.jobs.snapshots import canonical_hash
from conftest import sign_in

P = "/api/v1"


def queue(owner, app, monkeypatch, kind="research", **request):
    monkeypatch.setattr(app.state.runner, "submit", lambda jid: None)
    path = "/research-runs" if kind == "research" else "/backtests"
    response = owner.post(P + path, json=request)
    assert response.status_code == 202, response.text
    return response.json()["job_id"]


def test_research_freezes_evidence_and_export_is_private(owner, app, monkeypatch):
    jid = queue(owner, app, monkeypatch, instrument_id="DEMO_NOVA")
    snapshot = owner.get(P + f"/jobs/{jid}/snapshot").json()
    assert snapshot["snapshot_hash"] == canonical_hash(snapshot["payload"])
    assert snapshot["payload"]["events"]
    assert all(e["available_at"] for e in snapshot["payload"]["events"])
    with app.state.sessions() as db:
        for event in db.scalars(select(Event)):
            event.payload = {**event.payload, "summary": "A later correction", "instrument_ids": []}
        db.get(Instrument, "DEMO_NOVA").name = "Later instrument name"
        db.commit()
    app.state.runner.run(jid)
    job = owner.get(P + f"/jobs/{jid}").json()
    assert job["status"] == "SUCCEEDED", job
    assert job["result"]["instrument"] == snapshot["payload"]["instrument"]
    assert job["result"]["input_hash"] == snapshot["snapshot_hash"]
    assert "A later correction" not in str(job["result"])
    assert "_snapshot" not in job["input"]
    assert owner.get(P + f"/jobs/{jid}/snapshot").json() == snapshot
    sign_in(owner, "partner")
    assert owner.get(P + f"/jobs/{jid}/snapshot").status_code == 404
    assert owner.get(P + "/jobs").json() == []


def test_backtest_freezes_bars_and_strategy_at_submission(owner, app, monkeypatch):
    strategy = owner.get(P + "/strategies").json()[0]
    jid = queue(owner, app, monkeypatch, kind="backtest", strategy_version_id=strategy["id"])
    snapshot = owner.get(P + f"/jobs/{jid}/snapshot").json()
    with app.state.sessions() as db:
        row = db.get(Strategy, strategy["id"])
        row.spec = {**row.spec, "fast": 5}
        instrument = db.get(Instrument, row.spec["instrument_id"])
        changed = copy.deepcopy(instrument.bars)
        changed[0]["close"] = 999
        instrument.bars = changed
        db.commit()
    from app.quant.backtest import VectorbtResearchAdapter
    expected = VectorbtResearchAdapter().run(snapshot["payload"]["bars"], snapshot["payload"]["strategy"])
    app.state.runner.run(jid)
    job = owner.get(P + f"/jobs/{jid}").json()
    assert job["status"] == "SUCCEEDED", job
    for key in ["snapshot_hash", "final_equity", "orders", "equity"]:
        assert job["result"][key] == expected[key]
    assert job["result"]["input_hash"] == snapshot["snapshot_hash"]


def test_tampered_snapshot_fails_without_substitute(owner, app, monkeypatch):
    jid = queue(owner, app, monkeypatch, instrument_id="DEMO_NOVA")
    with app.state.sessions() as db:
        row = db.get(Job, jid)
        changed = copy.deepcopy(row.input)
        changed["_snapshot"]["events"] = []
        row.input = changed
        db.commit()
    response = owner.get(P + f"/jobs/{jid}/snapshot")
    assert response.status_code == 409
    assert response.json()["code"] == "SNAPSHOT_UNAVAILABLE"
    app.state.runner.run(jid)
    job = owner.get(P + f"/jobs/{jid}").json()
    assert job["status"] == "FAILED" and job["result"] is None


def test_zero_cutoff_and_duplicate_worker_claim(owner, app, monkeypatch):
    jid = queue(owner, app, monkeypatch, instrument_id="DEMO_NOVA", as_of=0)
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(app.state.runner.run, [jid, jid]))
    job = owner.get(P + f"/jobs/{jid}").json()
    assert job["status"] == "SUCCEEDED"
    assert job["result"]["as_of"] == 0
    assert job["result"]["evidence_ids"] == []
    with app.state.sessions() as db:
        assert len(list(db.scalars(select(Notification).where(Notification.id == f"notice-{jid}")))) == 1
    market = owner.get(P + "/market-data/DEMO_NOVA?as_of=0").json()
    assert market["as_of"] == 0 and market["bars"] == []


def test_legacy_pending_job_is_not_reconstructed_from_current_data(owner, app, monkeypatch):
    jid = queue(owner, app, monkeypatch, instrument_id="DEMO_NOVA")
    with app.state.sessions() as db:
        db.get(Job, jid).input = {"instrument_id": "DEMO_NOVA"}
        db.commit()
    app.state.runner.run(jid)
    job = owner.get(P + f"/jobs/{jid}").json()
    assert job["status"] == "FAILED" and job["result"] is None
    assert job["input"]["snapshot_hash"] is None
    assert owner.get(P + f"/jobs/{jid}/snapshot").status_code == 409
