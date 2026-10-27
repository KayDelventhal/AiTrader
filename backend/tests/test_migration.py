from pathlib import Path
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from app.db.models import Base


def test_frozen_migration_on_fresh_database(tmp_path, monkeypatch):
    import app.db.session as database
    engine = create_engine(f"sqlite:///{(tmp_path / 'migration.db').as_posix()}")
    monkeypatch.setattr(database, "engine", engine)
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    command.upgrade(config, "head")
    command.upgrade(config, "head")
    inspector = inspect(engine)
    assert set(Base.metadata.tables).issubset(inspector.get_table_names())
    for name, table in Base.metadata.tables.items():
        assert set(table.columns.keys()) == {column["name"] for column in inspector.get_columns(name)}
    engine.dispose()


def test_upgrade_preserves_existing_accounts_and_legacy_jobs(tmp_path, monkeypatch):
    import app.db.session as database
    engine = create_engine(f"sqlite:///{(tmp_path / 'existing.db').as_posix()}")
    monkeypatch.setattr(database, "engine", engine)
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    command.upgrade(config, "0001")
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO users (id,name,password) VALUES ('owner','Existing owner','untouched-password-hash')"))
        connection.execute(text("INSERT INTO accounts (id,owner_id,cash,positions,killed,revision) VALUES ('demo-owner','owner','9876.54','{}',0,7)"))
        connection.execute(text("INSERT INTO jobs (id,user_id,kind,status,created_at,input,result,error) VALUES ('legacy','owner','research','FAILED','2026-10-26T00:00:00+00:00','{}',NULL,'Previous result')"))
        before = {table: connection.execute(text(f"SELECT * FROM {table}")).fetchall() for table in ["users", "accounts", "jobs"]}
    command.upgrade(config, "head")
    command.upgrade(config, "head")
    with engine.connect() as connection:
        for table, expected in before.items():
            assert connection.execute(text(f"SELECT * FROM {table}")).fetchall() == expected
    engine.dispose()
