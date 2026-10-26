from typing import Literal
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, model_validator


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Login(Contract):
    username: str = Field(max_length=64)
    password: str = Field(max_length=256)


class StrategySpec(Contract):
    schema_version: Literal["1"] = "1"
    name: str = Field(min_length=3, max_length=100)
    hypothesis: str = Field(min_length=10, max_length=2000)
    instrument_id: str
    fast: int = Field(default=20, ge=2, le=100)
    slow: int = Field(default=50, ge=3, le=200)
    size: int = Field(default=2, ge=1, le=100)
    fees_bps: int = Field(default=10, ge=0, le=200)
    slippage_bps: int = Field(default=5, ge=0, le=200)
    strategy_id: str | None = None

    @model_validator(mode="after")
    def ordered(self):
        if self.fast >= self.slow:
            raise ValueError("Fast period must be smaller than slow period")
        return self


class BacktestRequest(Contract):
    strategy_version_id: str


class ResearchRequest(Contract):
    instrument_id: str
    as_of: int | None = None


class ProposalRequest(Contract):
    instrument_id: str
    side: Literal["BUY", "SELL"]
    quantity: int = Field(ge=1, le=100)


class ApprovalRequest(Contract):
    digest: str = Field(min_length=64, max_length=64)


class KillRequest(Contract):
    enabled: bool


class AnnotationRequest(Contract):
    instrument_id: str
    as_of: int
    price: Decimal = Field(gt=0, le=1000000, max_digits=12, decimal_places=4)
