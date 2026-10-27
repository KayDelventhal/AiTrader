from datetime import date
from typing import Annotated, Literal
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from pydantic import AwareDatetime, Field, field_validator, model_validator

from app.domain.contracts import Contract as RequestModel
from app.domain.responses import ResponseModel
from app.core.security import utcnow


Identifier = Annotated[str, Field(min_length=1, max_length=100)]
DomainIds = Annotated[list[Identifier], Field(min_length=1, max_length=30)]


def source_url(value):
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Use an HTTPS publication URL without credentials")
    return value


class GatheringDomainCreate(RequestModel):
    name: str = Field(min_length=2, max_length=100)
    description: str = Field(default="", max_length=1000)
    keywords: list[Annotated[str, Field(min_length=1, max_length=80)]] = Field(default_factory=list, max_length=40)
    enabled: bool = True

    @field_validator("name")
    @classmethod
    def trimmed(cls, value):
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Name must have at least two characters")
        return value

    @field_validator("keywords")
    @classmethod
    def unique_keywords(cls, value):
        cleaned = list(dict.fromkeys(word.strip() for word in value))
        if any(not word for word in cleaned):
            raise ValueError("Keywords cannot be blank")
        return cleaned


class GatheringDomainUpdate(GatheringDomainCreate):
    expected_revision: int = Field(ge=1)


class GatheringDomainView(ResponseModel):
    id: str
    name: str
    description: str
    keywords: list[str]
    enabled: bool
    revision: int


class GatheringSettingsUpdate(RequestModel):
    expected_revision: int = Field(ge=1)
    enabled: bool


class GatheringSettingsView(ResponseModel):
    revision: int
    enabled: bool
    schedule_note: str = "Collection runs only while this local application is running. Missed intervals are coalesced."


class GatheringSourceCreate(RequestModel):
    catalog_key: str = Field(min_length=1, max_length=80)
    domain_ids: DomainIds
    enabled: bool = False
    interval_minutes: int = Field(default=60, ge=15, le=10080)


class GatheringSourceUpdate(RequestModel):
    expected_revision: int = Field(ge=1)
    domain_ids: DomainIds
    enabled: bool
    interval_minutes: int = Field(ge=15, le=10080)


class GatheringCatalogEntry(ResponseModel):
    key: str
    name: str
    publisher: str
    url: str
    description: str
    reference_url: str = ""


class GatheringSourceView(ResponseModel):
    id: str
    catalog_key: str
    name: str
    publisher: str
    url: str
    domain_ids: list[str]
    enabled: bool
    interval_minutes: int
    revision: int
    next_due_at: str | None
    last_checked_at: str | None
    last_success_at: str | None
    last_error: str | None
    active_run_id: str | None


class GatheringConfig(ResponseModel):
    settings: GatheringSettingsView
    domains: list[GatheringDomainView]
    sources: list[GatheringSourceView]
    catalog: list[GatheringCatalogEntry]
    can_manage: bool
    network_allowed: bool


class GatheringRunView(ResponseModel):
    id: str
    source_id: str
    trigger: Literal["MANUAL", "SCHEDULED"]
    status: Literal["QUEUED", "RUNNING", "SUCCEEDED", "FAILED", "CANCELLED"]
    requested_by: str
    created_at: str
    started_at: str | None
    completed_at: str | None
    snapshot: dict
    counts: dict[str, int]
    metadata: dict
    error: str | None


class GatheringManualImport(RequestModel):
    idempotency_key: str = Field(min_length=8, max_length=120)
    publisher: str = Field(min_length=2, max_length=120)
    url: str = Field(min_length=8, max_length=2000)
    title: str = Field(min_length=3, max_length=500)
    text: str = Field(min_length=10, max_length=50000)
    domain_ids: DomainIds
    published_at: AwareDatetime | None = None
    published_on: date | None = None
    occurred_at: AwareDatetime | None = None
    note: str = Field(default="", max_length=1000)

    _url = field_validator("url")(source_url)

    @model_validator(mode="after")
    def publication_precision(self):
        if self.published_at is not None and self.published_on is not None:
            raise ValueError("Use either a publication timestamp or a publication date, not both")
        if self.published_on is not None and self.published_on > utcnow().astimezone(ZoneInfo("Europe/Berlin")).date():
            raise ValueError("A historical publication date cannot be in the future")
        return self


class GatheringRevisionView(ResponseModel):
    id: str
    document_id: str
    revision: int
    title: str
    content: str
    url: str
    publisher: str
    published_at: str | None
    published_on: date | None = None
    occurred_at: str | None
    source_updated_at: str | None
    recorded_at: str
    available_at: str
    content_hash: str
    domains: list[GatheringDomainView]
    domain_ids: list[str]
    original: dict
    attribution: str
    note: str


class GatheringDocumentView(ResponseModel):
    id: str
    source_id: str | None
    source_kind: Literal["RSS", "MANUAL"]
    first_seen_at: str
    revision: GatheringRevisionView


class GatheringDocumentDetail(ResponseModel):
    document: GatheringDocumentView
    revisions: list[GatheringRevisionView]


class GatheringDocumentPage(ResponseModel):
    items: list[GatheringDocumentView]
    total: int
    offset: int
    limit: int
    known_by: str | None


class GatheringImportResult(ResponseModel):
    document_id: str
    revision: int
    created: bool
    changed: bool
