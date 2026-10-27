from sqlalchemy import String, Text, Integer, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from app.core.security import iso_now


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    password: Mapped[str] = mapped_column(Text)


class SessionToken(Base):
    __tablename__ = "sessions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    csrf: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[str] = mapped_column(String(40))


class Instrument(Base):
    __tablename__ = "instruments"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    sector: Mapped[str] = mapped_column(String(80))
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    color: Mapped[str] = mapped_column(String(10))
    bars: Mapped[list] = mapped_column(JSON)


class Watch(Base):
    __tablename__ = "watchlist"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    instrument_id: Mapped[str] = mapped_column(ForeignKey("instruments.id"), primary_key=True)


class Event(Base):
    __tablename__ = "events"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    domain: Mapped[str] = mapped_column(String(80))
    available_at: Mapped[str] = mapped_column(String(40))
    payload: Mapped[dict] = mapped_column(JSON)


class Strategy(Base):
    __tablename__ = "strategy_versions"
    __table_args__ = (UniqueConstraint("strategy_id", "version"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    strategy_id: Mapped[str] = mapped_column(String(64))
    version: Mapped[int] = mapped_column(Integer)
    author_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[str] = mapped_column(String(40), default=iso_now)
    spec: Mapped[dict] = mapped_column(JSON)


class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    kind: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(30), default="PENDING")
    created_at: Mapped[str] = mapped_column(String(40), default=iso_now)
    input: Mapped[dict] = mapped_column(JSON)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class Account(Base):
    __tablename__ = "accounts"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    cash: Mapped[str] = mapped_column(String(40), default="10000.00")
    positions: Mapped[dict] = mapped_column(JSON, default=dict)
    killed: Mapped[int] = mapped_column(Integer, default=0)
    revision: Mapped[int] = mapped_column(Integer, default=0)


class Proposal(Base):
    __tablename__ = "proposals"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"))
    payload: Mapped[dict] = mapped_column(JSON)
    digest: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(30), default="AWAITING_APPROVAL")
    created_at: Mapped[str] = mapped_column(String(40), default=iso_now)
    expires_at: Mapped[str] = mapped_column(String(40))
    fill: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class Audit(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor_id: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(80))
    object_id: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[str] = mapped_column(String(40), default=iso_now)
    detail: Mapped[dict] = mapped_column(JSON, default=dict)


class Annotation(Base):
    __tablename__ = "annotations"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    instrument_id: Mapped[str] = mapped_column(ForeignKey("instruments.id"))
    created_at: Mapped[str] = mapped_column(String(40), default=iso_now)
    as_of: Mapped[int] = mapped_column(Integer)
    price: Mapped[str] = mapped_column(String(40))


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[str] = mapped_column(String(40), default=iso_now)
    message: Mapped[str] = mapped_column(Text)
    read: Mapped[int] = mapped_column(Integer, default=0)


class WorkspaceSettings(Base):
    __tablename__ = "workspace_settings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    markets: Mapped[list] = mapped_column(JSON)
    horizon: Mapped[str] = mapped_column(String(30))
    monthly_limit_micros: Mapped[int] = mapped_column(Integer)
    warning_pct: Mapped[int] = mapped_column(Integer, default=80)
    updated_at: Mapped[str] = mapped_column(String(40), default=iso_now)


class WorkspaceSettingsRevision(Base):
    __tablename__ = "workspace_settings_revisions"
    revision: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_id: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[str] = mapped_column(String(40), default=iso_now)
    payload: Mapped[dict] = mapped_column(JSON)


class BudgetMonth(Base):
    __tablename__ = "budget_months"
    month: Mapped[str] = mapped_column(String(7), primary_key=True)
    limit_micros: Mapped[int] = mapped_column(Integer)
    settings_revision: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[str] = mapped_column(String(40), default=iso_now)


class CostEntry(Base):
    __tablename__ = "cost_entries"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String(160), unique=True)
    request_hash: Mapped[str] = mapped_column(String(64))
    month: Mapped[str] = mapped_column(ForeignKey("budget_months.month"), index=True)
    provider: Mapped[str] = mapped_column(String(80))
    category: Mapped[str] = mapped_column(String(30))
    description: Mapped[str] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(20))
    amount_micros: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reserved_micros: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(3))
    original_amount: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fx_rate: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fx_as_of: Mapped[str | None] = mapped_column(String(40), nullable=True)
    pricing_version: Mapped[str] = mapped_column(String(120))
    run_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    strategy_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source: Mapped[str] = mapped_column(String(20))
    revision: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[str] = mapped_column(String(40), default=iso_now)


class CostRevision(Base):
    __tablename__ = "cost_revisions"
    __table_args__ = (UniqueConstraint("entry_id", "event_key"), UniqueConstraint("entry_id", "revision"))
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entry_id: Mapped[str] = mapped_column(ForeignKey("cost_entries.id"))
    event_key: Mapped[str] = mapped_column(String(120))
    request_hash: Mapped[str] = mapped_column(String(64))
    revision: Mapped[int] = mapped_column(Integer)
    actor_id: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[str] = mapped_column(String(40), default=iso_now)
    note: Mapped[str] = mapped_column(String(500))
    payload: Mapped[dict] = mapped_column(JSON)


class RecurringCost(Base):
    __tablename__ = "recurring_costs"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String(120), unique=True)
    request_hash: Mapped[str] = mapped_column(String(64))
    provider: Mapped[str] = mapped_column(String(80))
    category: Mapped[str] = mapped_column(String(30))
    description: Mapped[str] = mapped_column(String(300))
    monthly_amount_micros: Mapped[int] = mapped_column(Integer)
    start_month: Mapped[str] = mapped_column(String(7))
    end_month: Mapped[str | None] = mapped_column(String(7), nullable=True)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    stop_event_key: Mapped[str | None] = mapped_column(String(120), nullable=True)
    stop_request_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[str] = mapped_column(String(40), default=iso_now)
