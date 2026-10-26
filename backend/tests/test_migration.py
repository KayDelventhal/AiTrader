from pathlib import Path
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
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
