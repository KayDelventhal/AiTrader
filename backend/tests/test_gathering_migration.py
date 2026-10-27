"""Upgrade an existing cost-accounting workspace without rewriting its history."""
from collections import Counter
import json
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from app.db.seed import seed


def _tables(connection):
    return [row[0] for row in connection.execute(text("SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name != 'alembic_version'"))]


def _contents(connection, tables):
    return {name: Counter(connection.execute(text('SELECT * FROM "' + name.replace('"', '""') + '"')).fetchall()) for name in tables}


def test_gathering_upgrade_preserves_populated_workspace_costs_and_history(tmp_path, monkeypatch):
    import app.db.session as database
    engine = create_engine(f"sqlite:///{(tmp_path / 'existing-costs.db').as_posix()}")
    monkeypatch.setattr(database, "engine", engine)
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    command.upgrade(config, "0002_workspace_costs")
    timestamp = "2025-01-15T10:00:00+00:00"
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO users (id,name,password) VALUES ('owner','Existing owner','untouched-hash')"))
        connection.execute(text("INSERT INTO accounts (id,owner_id,cash,positions,killed,revision) VALUES ('demo-owner','owner','9876.54','{}',0,7)"))
        connection.execute(text("INSERT INTO workspace_settings (id,revision,markets,horizon,monthly_limit_micros,warning_pct,updated_at) VALUES (1,2,'[\"US\",\"EU\"]','weeks_months',23000000,80,:at)"), {"at": timestamp})
        settings = {"revision": 2, "markets": ["US", "EU"], "horizon": "weeks_months", "monthly_limit_eur": "23.000000", "warning_pct": 80}
        connection.execute(text("INSERT INTO workspace_settings_revisions (revision,actor_id,created_at,payload) VALUES (2,'owner',:at,:payload)"), {"at": timestamp, "payload": json.dumps(settings)})
        connection.execute(text("INSERT INTO budget_months (month,limit_micros,settings_revision,created_at) VALUES ('2025-01',23000000,2,:at)"), {"at": timestamp})
        connection.execute(text("INSERT INTO cost_entries (id,idempotency_key,request_hash,month,provider,category,description,status,amount_micros,reserved_micros,currency,original_amount,fx_rate,fx_as_of,pricing_version,run_id,strategy_id,source,revision,created_at) VALUES ('invoice','existing-invoice','existing-hash','2025-01','Historical provider','AI','Existing paid usage','CONFIRMED',1234567,0,'EUR','1.234567','1',NULL,'existing-price',NULL,NULL,'manual',2,:at)"), {"at": timestamp})
        for revision, amount in [(1, "1.000000"), (2, "1.234567")]:
            payload = {"status": "CONFIRMED", "amount_eur": amount, "currency": "EUR"}
            connection.execute(text("INSERT INTO cost_revisions (entry_id,event_key,request_hash,revision,actor_id,created_at,note,payload) VALUES ('invoice',:event,'hash',:revision,'owner',:at,'Existing bill history',:payload)"), {"event": f"event-{revision}", "revision": revision, "at": timestamp, "payload": json.dumps(payload)})
        connection.execute(text("INSERT INTO recurring_costs (id,idempotency_key,request_hash,provider,category,description,monthly_amount_micros,start_month,end_month,revision,stop_event_key,stop_request_hash,created_at) VALUES ('plan','existing-plan','hash','Feed provider','MARKET_DATA','Stopped commitment',5000000,'2025-01','2025-02',2,'stopped','stop-hash',:at)"), {"at": timestamp})
        connection.execute(text("INSERT INTO audit_events (actor_id,action,object_id,created_at,detail) VALUES ('owner','EXISTING_AUDIT','invoice',:at,:detail)"), {"at": timestamp, "detail": json.dumps({"preserve": True})})
        old_tables = _tables(connection)
        before = _contents(connection, old_tables)
    assert "gathering_settings" not in inspect(engine).get_table_names()

    command.upgrade(config, "head")
    sessions = sessionmaker(engine)
    with sessions() as db:
        seed(db)
    with engine.connect() as connection:
        assert _contents(connection, old_tables) == before
        assert connection.execute(text("SELECT enabled, revision FROM gathering_settings")).fetchone() == (0, 1)
        assert set(connection.execute(text("SELECT name FROM research_domains")).scalars()) == {"Nvidia", "Amazon", "Macroeconomics", "Geopolitics"}
        assert connection.execute(text("SELECT COUNT(*) FROM gathering_sources")).scalar() == 0
        assert connection.execute(text("SELECT COUNT(*) FROM research_documents")).scalar() == 0
        assert connection.execute(text("PRAGMA integrity_check")).scalar() == "ok"
        assert connection.execute(text("PRAGMA foreign_key_check")).fetchall() == []
        all_tables = _tables(connection)
        first_upgrade = _contents(connection, all_tables)

    command.upgrade(config, "head")
    with sessions() as db:
        seed(db)
    with engine.connect() as connection:
        assert _contents(connection, all_tables) == first_upgrade
    engine.dispose()
