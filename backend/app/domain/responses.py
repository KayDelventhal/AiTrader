"""Public response contracts: never serialize ORM internals or secret fields."""
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, AwareDatetime

DecimalString = Annotated[str, Field(pattern=r"^-?\d+(\.\d+)?$")]


class ResponseModel(BaseModel):
    model_config = ConfigDict(extra="ignore", from_attributes=True)
    schema_version: Literal["1"] = "1"


class Health(ResponseModel):
    status: Literal["ok"]
    mode: Literal["DEMO"]
    instance_id: str


class UserView(ResponseModel):
    id: str
    name: str
    csrf: str


class Ok(ResponseModel):
    ok: bool


class WatchResult(ResponseModel):
    watched: bool


class KillResult(ResponseModel):
    enabled: bool


class RejectResult(ResponseModel):
    status: Literal["REJECTED"]


class InstrumentView(ResponseModel):
    id: str
    symbol: str
    name: str
    sector: str
    currency: Literal["EUR"]
    color: str
    price: DecimalString
    change_pct: float
    as_of: int
    source: str
    watched: bool
    sparkline: list[float]
    broker_capable: Literal[False]


class BarView(BaseModel):
    time: int
    open: float
    high: float
    low: float
    close: float
    volume: int
    final: bool
    available_at: AwareDatetime
    revision: int


class Point(BaseModel):
    time: int
    value: float


class MarketDataView(ResponseModel):
    instrument_id: str
    bars: list[BarView]
    indicators: dict[str, list[Point]]
    source: str
    currency: Literal["EUR"]
    interval: Literal["1d"]
    mode: Literal["DEMO"]
    as_of: int
    first_time: int
    last_time: int
    total_bars: int
    quality: str


class EvidenceView(BaseModel):
    id: str
    publisher: str
    title: str
    revision: int
    type: Literal["fixture"]
    independent_origins: int
    copies: int
    available_at: AwareDatetime


class EventContent(BaseModel):
    id: str
    title: str
    status: str
    severity: str
    instrument_ids: list[str]
    summary: str
    mechanism: list[str]
    counterargument: str
    evidence: list[EvidenceView]
    next_check: str
    claim_type: str


class EventView(EventContent, ResponseModel):
    domain: str
    available_at: AwareDatetime


class StrategyDetails(BaseModel):
    schema_version: Literal["1"] = "1"
    name: str
    hypothesis: str
    instrument_id: str
    fast: int
    slow: int
    size: int
    fees_bps: int
    slippage_bps: int
    status: Literal["draft"]
    horizon: Literal["intraday", "days_weeks", "weeks_months"] | None = None


class StrategyView(ResponseModel):
    id: str
    strategy_id: str
    version: int
    author_id: str
    created_at: AwareDatetime
    spec: StrategyDetails


class BacktestOrder(BaseModel):
    time: int
    signal_time: int
    side: Literal["BUY", "SELL"]
    quantity: float
    price: float
    fees: float


class BacktestResult(ResponseModel):
    engine: Literal["vectorbt"]
    engine_version: str
    dataset: str
    snapshot_hash: str
    input_hash: str | None = None
    strategy_version_id: str
    currency: Literal["EUR"]
    initial_cash: DecimalString
    final_equity: float
    return_pct: float
    max_drawdown_pct: float
    closed_trades: int
    win_rate_pct: float | None
    stress_return_pct: float
    orders: list[BacktestOrder]
    equity: list[Point]
    benchmark: list[Point]
    assumptions: list[str]


class ResearchInstrument(BaseModel):
    id: str
    name: str


class ResearchResult(ResponseModel):
    instrument: ResearchInstrument
    events: list[EventContent]
    evidence_ids: list[str]
    findings: list[str]
    counterarguments: list[str]
    conclusion: str
    steps: list[str]
    provider: str
    model_calls: Literal[0]
    cost_eur: DecimalString
    evaluation_mode: Literal["DEMO"]
    as_of: int
    input_hash: str | None = None


class JobInput(BaseModel):
    """Public input references. Large frozen payloads require the snapshot endpoint."""
    strategy_version_id: str | None = None
    instrument_id: str | None = None
    as_of: int | None = None
    snapshot_hash: str | None = None
    snapshot_version: Literal["1"] | None = None
    horizon: Literal["intraday", "days_weeks", "weeks_months"] | None = None
    settings_revision: int | None = None


class JobBase(ResponseModel):
    id: str
    user_id: str
    status: Literal["PENDING", "RUNNING", "SUCCEEDED", "FAILED"]
    created_at: AwareDatetime
    input: JobInput
    error: str | None


class BacktestJob(JobBase):
    kind: Literal["backtest"]
    result: BacktestResult | None


class ResearchJob(JobBase):
    kind: Literal["research"]
    result: ResearchResult | None


JobView = Annotated[BacktestJob | ResearchJob, Field(discriminator="kind")]


class JobQueued(ResponseModel):
    job_id: str
    status: Literal["PENDING"]


class InputSnapshot(ResponseModel):
    job_id: str
    snapshot_hash: str
    captured_at: AwareDatetime
    payload: dict[str, Any]


class PositionView(BaseModel):
    quantity: int
    cost_basis: DecimalString
    realized_pnl: DecimalString


class AccountView(ResponseModel):
    id: str
    owner_id: str
    cash: DecimalString
    positions: dict[str, PositionView]
    killed: Literal[0, 1]
    revision: int


class OrderPayload(BaseModel):
    schema_version: Literal["1"]
    account_id: str
    account_revision: int
    environment: Literal["LOCAL_DEMO"]
    instrument_id: str
    symbol: str
    side: Literal["BUY", "SELL"]
    quantity: int
    order_type: Literal["FIXTURE_SNAPSHOT"]
    price: DecimalString
    fee: DecimalString
    currency: Literal["EUR"]
    source: str
    reference_time: int
    reference_price: DecimalString
    fill_assumption: str


class FillView(OrderPayload):
    id: str
    at: AwareDatetime


class ProposalView(ResponseModel):
    id: str
    user_id: str
    account_id: str
    payload: OrderPayload
    digest: str
    status: Literal["AWAITING_APPROVAL", "FILLED", "REJECTED", "EXPIRED"]
    created_at: AwareDatetime
    expires_at: AwareDatetime
    fill: FillView | None


class AuditView(ResponseModel):
    id: int
    actor_id: str
    action: str
    object_id: str
    created_at: AwareDatetime
    detail: dict[str, Any]


class AnnotationView(ResponseModel):
    id: str
    user_id: str
    instrument_id: str
    created_at: AwareDatetime
    as_of: int
    price: DecimalString


class NotificationView(ResponseModel):
    id: str
    user_id: str
    created_at: AwareDatetime
    message: str
    read: Literal[0, 1]


class ServiceView(BaseModel):
    name: str
    status: str
    detail: str


class SystemStatusView(ResponseModel):
    mode: Literal["DEMO"]
    database: str
    external_requests: bool
    live_enabled: Literal[False]
    timezone: str
    currency: Literal["EUR"]
    worker: str
    services: list[ServiceView]


class ValidationIssue(BaseModel):
    location: list[str | int]
    code: str


class ErrorResponse(ResponseModel):
    code: str
    detail: str
    request_id: str
    issues: list[ValidationIssue] = Field(default_factory=list)
