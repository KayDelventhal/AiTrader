from sqlalchemy import select
from app.core.config import settings
from app.core.security import password_hash
from app.db.models import User, Account, Instrument, Watch, Event, Strategy, Audit
from app.marketdata.demo import generate_bars


def seed(db):
    from app.workspace.service import seed_workspace
    seed_workspace(db)
    if db.get(User, "owner"):
        return
    for uid, name, password in [("owner", "Alex Morgan", settings.demo_owner_password), ("partner", "Sam Taylor", settings.demo_partner_password)]:
        db.add(User(id=uid, name=name, password=password_hash(password)))
    db.flush()
    for uid in ["owner", "partner"]:
        db.add(Account(id=f"demo-{uid}", owner_id=uid, cash="10000.00", positions={}))
    instruments = [("DEMO_NOVA", "NOVA", "Nova Systems", "AI & technology", "#76a9ff", 7, 118), ("DEMO_AURORA", "AURA", "Aurora Energy", "Energy & transport", "#c4b5fd", 12, 64), ("DEMO_SILICA", "SLCA", "Silica Industries", "Semiconductors", "#f5c879", 19, 86), ("DEMO_ATLAS", "ATLS", "Atlas Diversified ETF", "Diversified", "#6dd5b0", 29, 42)]
    for iid, symbol, name, sector, color, seed_value, base in instruments:
        db.add(Instrument(id=iid, symbol=symbol, name=name, sector=sector, color=color, bars=generate_bars(seed_value, base)))
    db.flush()
    for uid in ["owner", "partner"]:
        for iid, *_ in instruments:
            db.add(Watch(user_id=uid, instrument_id=iid))
    fixtures = [
        ("energy-route", "Transport disruption puts energy costs in focus", "Energy", "2026-10-20T14:00:00+00:00", {
            "status": "OBSERVED", "severity": "Elevated", "instrument_ids": ["DEMO_AURORA", "DEMO_SILICA"], "summary": "A fictional shipping advisory describes delays on the North Passage. Higher transport costs could affect energy-intensive manufacturers.", "mechanism": ["Transport capacity tightens", "Freight and insurance costs may rise", "Input costs pressure manufacturers"], "counterargument": "Available inventory and alternative routes could absorb the disruption. No confirmed production impact is recorded.", "evidence": [{"id": "E-ENERGY-1", "publisher": "Demo Maritime Bulletin", "title": "North Passage capacity advisory", "revision": 1, "type": "fixture", "independent_origins": 1, "copies": 3, "available_at": "2026-10-20T14:00:00+00:00"}], "next_check": "Look for an independent capacity update.", "claim_type": "scenario"}),
        ("ai-efficiency", "New model efficiency opens a cost hypothesis", "Technology", "2026-10-21T10:00:00+00:00", {
            "status": "UNCONFIRMED", "severity": "Watch", "instrument_ids": ["DEMO_NOVA"], "summary": "A fictional lab reports lower inference costs. Independent replication is missing; the impact on software margins remains a hypothesis.", "mechanism": ["Compute per task could decline", "Application delivery costs may fall", "Competitive pricing may offset margin gains"], "counterargument": "Vendor benchmarks may not reflect production workloads. Savings could be passed directly to customers.", "evidence": [{"id": "E-AI-1", "publisher": "Demo Model Lab", "title": "Efficiency benchmark release", "revision": 1, "type": "fixture", "independent_origins": 1, "copies": 1, "available_at": "2026-10-21T10:00:00+00:00"}], "next_check": "Wait for independent benchmark replication.", "claim_type": "hypothesis"}),
        ("chip-input", "Chip input availability needs a second source", "Supply chains", "2026-10-22T09:00:00+00:00", {
            "status": "OBSERVED", "severity": "Elevated", "instrument_ids": ["DEMO_SILICA", "DEMO_NOVA"], "summary": "A fictional supplier extends lead times for a chip precursor. The downstream effect depends on inventory cover and substitution.", "mechanism": ["Precursor lead times increase", "Fabrication schedules may tighten", "Hardware delivery assumptions need review"], "counterargument": "The notice concerns one supplier. Alternative sourcing and inventory are not yet documented.", "evidence": [{"id": "E-CHIP-1", "publisher": "Demo Materials Monitor", "title": "Precursor lead-time notice", "revision": 1, "type": "fixture", "independent_origins": 1, "copies": 2, "available_at": "2026-10-22T09:00:00+00:00"}], "next_check": "Check inventory cover and a second supplier.", "claim_type": "scenario"})]
    for eid, title, domain, available, payload in fixtures:
        db.add(Event(id=eid, title=title, domain=domain, available_at=available, payload=payload))
    db.add(Strategy(id="strategy-trend-v1", strategy_id="strategy-trend", version=1, author_id="owner", spec={"schema_version": "1", "name": "Measured momentum", "hypothesis": "Persistent trends may continue while energy costs remain stable. A fast/slow moving-average crossover tests this fictional hypothesis.", "instrument_id": "DEMO_NOVA", "fast": 20, "slow": 50, "size": 2, "fees_bps": 10, "slippage_bps": 5, "status": "draft"}))
    db.add(Audit(actor_id="system", action="DEMO_INITIALIZED", object_id="fixture-v1", detail={"fictional": True, "external_requests": False}))
    db.commit()
