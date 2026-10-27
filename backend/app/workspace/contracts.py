from decimal import Decimal
from typing import Annotated, Literal
from pydantic import AwareDatetime, Field, model_validator
from app.domain.contracts import Contract
from app.domain.responses import ResponseModel

Horizon = Literal["intraday", "days_weeks", "weeks_months"]
Category = Literal["AI", "SEARCH_NEWS", "MARKET_DATA"]
Money = Annotated[Decimal, Field(ge=0, le=100000, decimal_places=6, allow_inf_nan=False)]
Month = Annotated[str, Field(pattern=r"^(20\d{2}|2100)-(0[1-9]|1[0-2])$")]
Key = Annotated[str, Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_.:/-]+$")]


class WorkspaceSettingsUpdate(Contract):
    expected_revision: int = Field(ge=1)
    markets: list[Literal["US", "EU"]] = Field(min_length=1, max_length=2)
    horizon: Horizon
    monthly_limit_eur: Money
    warning_pct: int = Field(default=80, ge=1, le=100)

    @model_validator(mode="after")
    def unique_markets(self):
        if len(set(self.markets)) != len(self.markets):
            raise ValueError("Markets must be unique")
        return self


class WorkspaceSettingsView(ResponseModel):
    revision: int
    markets: list[Literal["US", "EU"]]
    horizon: Horizon
    monthly_limit_eur: str
    warning_pct: int
    can_manage: bool


class CostMetadata(Contract):
    provider: str = Field(min_length=1, max_length=80)
    category: Category
    description: str = Field(min_length=1, max_length=300)


class CostAmount(Contract):
    amount: Money | None = None
    currency: str = Field(default="EUR", pattern=r"^[A-Z]{3}$")
    fx_rate: Annotated[Decimal, Field(gt=0, le=100000, decimal_places=10, allow_inf_nan=False)] | None = None
    fx_as_of: AwareDatetime | None = None
    pricing_version: str = Field(min_length=1, max_length=120)

    @model_validator(mode="after")
    def conversion(self):
        if self.currency == "EUR":
            if self.fx_rate not in (None, Decimal(1)):
                raise ValueError("EUR conversion must be one")
        elif self.amount is not None and (self.fx_rate is None or self.fx_as_of is None):
            raise ValueError("Non-EUR amounts require a dated EUR conversion basis")
        if self.amount is not None and self.amount * (self.fx_rate or Decimal(1)) > Decimal(100000):
            raise ValueError("Converted amount exceeds supported bound")
        return self


class ManualCost(CostAmount, CostMetadata):
    idempotency_key: Key
    month: Month | None = None
    status: Literal["CONFIRMED", "ESTIMATED", "UNCERTAIN"]
    run_id: str | None = Field(default=None, max_length=64)
    strategy_id: str | None = Field(default=None, max_length=64)

    @model_validator(mode="after")
    def status_amount(self):
        if (self.status == "UNCERTAIN") != (self.amount is None):
            raise ValueError("Unknown amounts require UNCERTAIN; priced expenses require an amount")
        return self


class ReserveCost(CostMetadata):
    idempotency_key: Key
    max_cost_eur: Money = Field(gt=0)
    run_id: str | None = Field(default=None, max_length=64)
    strategy_id: str | None = Field(default=None, max_length=64)


class ReconcileCost(CostAmount):
    event_key: Key
    expected_revision: int = Field(ge=1)
    status: Literal["CONFIRMED", "ESTIMATED", "UNCERTAIN", "CANCELLED"]
    note: str = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def status_amount(self):
        if self.status in {"CONFIRMED", "ESTIMATED"} and self.amount is None:
            raise ValueError("A priced result requires an amount")
        if self.status == "UNCERTAIN" and self.amount is not None:
            raise ValueError("Use ESTIMATED for an estimated amount")
        if self.status == "CANCELLED" and self.amount not in (None, Decimal(0)):
            raise ValueError("Cancelled reservations cannot retain a charge")
        return self


class RecurringCostCreate(CostMetadata):
    idempotency_key: Key
    monthly_amount_eur: Money = Field(gt=0)
    start_month: Month | None = None


class StopRecurringCost(Contract):
    expected_revision: int = Field(ge=1)
    event_key: Key


class CostRevisionView(ResponseModel):
    revision: int
    event_key: str
    actor_id: str
    created_at: AwareDatetime
    note: str
    payload: dict


class CostEntryView(ResponseModel):
    id: str
    month: str
    provider: str
    category: Category
    description: str
    status: Literal["RESERVED", "UNCERTAIN", "ESTIMATED", "CONFIRMED", "CANCELLED"]
    amount_eur: str | None
    reserved_eur: str
    currency: str
    original_amount: str | None
    fx_rate: str | None
    fx_as_of: AwareDatetime | None
    pricing_version: str
    run_id: str | None
    strategy_id: str | None
    source: Literal["manual", "reservation", "recurring"]
    revision: int
    created_at: AwareDatetime
    history: list[CostRevisionView]


class RecurringCostView(ResponseModel):
    id: str
    provider: str
    category: Category
    description: str
    monthly_amount_eur: str
    start_month: str
    end_month: str | None
    revision: int


class CostBreakdown(ResponseModel):
    provider: str
    category: Category
    confirmed_eur: str
    estimated_eur: str
    reserved_eur: str
    has_unknown: bool


class CostSummary(ResponseModel):
    month: str
    current_month: str
    limit_eur: str
    confirmed_eur: str
    estimated_eur: str
    reserved_eur: str
    carryover_reserved_eur: str
    remaining_eur: str
    available_eur: str
    status: Literal["OK", "WARNING", "EXHAUSTED", "OVER_BUDGET", "UNKNOWN_COST"]
    has_unknown: bool
    can_manage: bool
    entries: list[CostEntryView]
    breakdown: list[CostBreakdown]
    recurring: list[RecurringCostView]
