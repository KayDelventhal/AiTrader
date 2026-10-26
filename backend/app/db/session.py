from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.core.config import ROOT, settings


def make_engine(url: str | None = None):
    (ROOT / ".runtime").mkdir(exist_ok=True)
    url = url or settings.database_url or f"sqlite:///{(ROOT / '.runtime' / 'aitrader.db').as_posix()}"
    engine = create_engine(url, connect_args={"check_same_thread": False, "timeout": 30} if url.startswith("sqlite") else {}, pool_pre_ping=True)
    if url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def configure(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA journal_mode=WAL")
    return engine


engine = make_engine()
SessionLocal = sessionmaker(engine, expire_on_commit=False)
