"""Local research library with explicit collection gates and immutable revisions.

The singleton write lock serializes source claims, configuration and imports.
Network work happens only after a committed claim, outside this service.
"""
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import hashlib
import json
import uuid
from urllib.parse import urlsplit, urlunsplit

from sqlalchemy import select, update, func, and_, or_

from app.core.config import settings
from app.core.errors import ApiError
from app.core.security import utcnow
from app.db.models import (Audit, GatheringSettings, ResearchDomain, GatheringSource,
    GatheringRun, ResearchDocument, ResearchDocumentRevision, GatheringImport)
from app.gathering.catalog import CATALOG


SEED_DOMAINS = [
    ("nvidia", "Nvidia", "Nvidia research, including semiconductor supply chains, AI demand, energy availability and export controls.", ["Nvidia", "semiconductors", "AI", "data centers", "export controls", "electricity"]),
    ("amazon", "Amazon", "Amazon research, including AWS, retail demand, logistics, labor costs and regulation.", ["Amazon", "AWS", "cloud", "retail", "logistics", "consumer spending"]),
    ("macroeconomics", "Macroeconomics", "Monetary policy, inflation, employment, growth and financial conditions across markets.", ["interest rates", "inflation", "employment", "growth", "central bank"]),
    ("geopolitics", "Geopolitics", "Political decisions, trade restrictions, energy routes and supply-chain risks with indirect market influence.", ["trade", "sanctions", "supply chains", "energy", "export controls", "geopolitics"]),
]


def _now():
    return utcnow().astimezone(timezone.utc).isoformat()


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def _owner(actor_id):
    if actor_id != "owner":
        raise ApiError(403, "GATHERING_OWNER_REQUIRED", "Only the workspace owner can change research gathering.")


def seed_gathering(db):
    if db.get(GatheringSettings, 1) is None:
        db.add(GatheringSettings(id=1, revision=1, enabled=False))
        for did, name, description, keywords in SEED_DOMAINS:
            db.add(ResearchDomain(id=did, name=name, description=description, keywords=keywords, enabled=True, revision=1))
        db.commit()


@contextmanager
def _locked(db):
    try:
        changed = db.execute(update(GatheringSettings).where(GatheringSettings.id == 1).values(revision=GatheringSettings.revision))
        if changed.rowcount != 1:
            raise ApiError(503, "GATHERING_NOT_INITIALIZED", "Run migrations and seed the research library first.")
        db.expire_all()
        yield
        db.commit()
    except BaseException:
        db.rollback()
        raise


def _audit(db, actor_id, action, object_id, detail):
    db.add(Audit(actor_id=actor_id, action=action, object_id=object_id, detail=detail))


def _domain_view(row):
    return {"id": row.id, "name": row.name, "description": row.description,
            "keywords": list(row.keywords), "enabled": row.enabled, "revision": row.revision}


def _source_view(row):
    catalog = CATALOG.get(row.catalog_key, {})
    return {"id": row.id, "catalog_key": row.catalog_key, "name": catalog.get("name", "Unavailable source"),
            "publisher": catalog.get("publisher", "Unknown publisher"), "url": catalog.get("url", ""),
            **{key: getattr(row, key) for key in ["enabled", "interval_minutes", "revision", "next_due_at",
                "last_checked_at", "last_success_at", "last_error", "active_run_id"]}, "domain_ids": list(row.domain_ids)}


def _settings_view(row):
    return {"enabled": row.enabled, "revision": row.revision}


def get_config(db, user_id):
    row = db.get(GatheringSettings, 1)
    if row is None:
        raise ApiError(503, "GATHERING_NOT_INITIALIZED", "Run migrations and seed the research library first.")
    return {"settings": _settings_view(row), "domains": [_domain_view(d) for d in db.scalars(select(ResearchDomain).order_by(ResearchDomain.created_at, ResearchDomain.id))],
            "sources": [_source_view(s) for s in db.scalars(select(GatheringSource).order_by(GatheringSource.created_at, GatheringSource.id))],
            "catalog": list(CATALOG.values()), "can_manage": user_id == "owner", "network_allowed": settings.public_feed_requests_allowed}


def update_settings(db, actor_id, request):
    _owner(actor_id)
    with _locked(db):
        row = db.get(GatheringSettings, 1)
        if row.revision != request.expected_revision:
            raise ApiError(409, "GATHERING_SETTINGS_CHANGED", "Gathering settings changed. Refresh before saving.")
        row.enabled, row.revision = request.enabled, row.revision + 1
        _audit(db, actor_id, "GATHERING_SETTINGS_CHANGED", "gathering", _settings_view(row))
        return _settings_view(row)


def save_domain(db, actor_id, request, domain_id=None):
    _owner(actor_id)
    with _locked(db):
        row = db.get(ResearchDomain, domain_id) if domain_id else None
        if domain_id and not row:
            raise ApiError(404, "DOMAIN_NOT_FOUND", "Research domain not found.")
        if row and row.revision != request.expected_revision:
            raise ApiError(409, "DOMAIN_CHANGED", "Research domain changed. Refresh before saving.")
        name = request.name.strip()
        if any(d.id != domain_id and d.name.casefold() == name.casefold() for d in db.scalars(select(ResearchDomain))):
            raise ApiError(409, "DOMAIN_NAME_EXISTS", "A research domain with this name already exists.")
        if row is None:
            if len(list(db.scalars(select(ResearchDomain.id)))) >= 30:
                raise ApiError(422, "DOMAIN_LIMIT_REACHED", "This local workspace supports up to 30 research domains.")
            row = ResearchDomain(id=uuid.uuid4().hex, revision=0)
            db.add(row)
        row.name, row.description, row.keywords = name, request.description.strip(), request.keywords
        row.enabled, row.revision, row.updated_at = request.enabled, row.revision + 1, _now()
        _audit(db, actor_id, "RESEARCH_DOMAIN_SAVED", row.id, _domain_view(row))
        return _domain_view(row)


def _domains(db, ids):
    ids = list(dict.fromkeys(ids))
    rows = [db.get(ResearchDomain, did) for did in ids]
    if not ids or any(row is None for row in rows):
        raise ApiError(422, "INVALID_RESEARCH_DOMAINS", "Choose at least one existing research domain.")
    return [_domain_view(row) for row in rows]


def save_source(db, actor_id, request, source_id=None):
    _owner(actor_id)
    with _locked(db):
        domains = _domains(db, request.domain_ids)
        row = db.get(GatheringSource, source_id) if source_id else None
        if source_id and row is None:
            raise ApiError(404, "SOURCE_NOT_FOUND", "Research source not found.")
        if row and row.revision != request.expected_revision:
            raise ApiError(409, "SOURCE_CHANGED", "Research source changed. Refresh before saving.")
        if row is None:
            if request.catalog_key not in CATALOG:
                raise ApiError(422, "UNSUPPORTED_SOURCE", "Choose a supported public source from the catalog.")
            if db.scalar(select(GatheringSource.id).where(GatheringSource.catalog_key == request.catalog_key)):
                raise ApiError(409, "SOURCE_EXISTS", "This source is already configured. Edit its domains instead.")
            row = GatheringSource(id=uuid.uuid4().hex, catalog_key=request.catalog_key, revision=0)
            db.add(row)
        row.domain_ids = [d["id"] for d in domains]
        row.enabled, row.interval_minutes = request.enabled, request.interval_minutes
        row.revision, row.updated_at = row.revision + 1, _now()
        if row.next_due_at is None:
            row.next_due_at = _now()
        _audit(db, actor_id, "GATHERING_SOURCE_SAVED", row.id, _source_view(row))
        return _source_view(row)


def run_view(row):
    return {key: getattr(row, key) for key in ["id", "source_id", "trigger", "status", "requested_by", "created_at", "started_at", "completed_at", "snapshot", "counts", "error"]} | {"metadata": row.result_metadata}


def list_runs(db):
    return [run_view(row) for row in db.scalars(select(GatheringRun).order_by(GatheringRun.created_at.desc(), GatheringRun.id.desc()).limit(50))]


def _can_collect(db, source):
    return bool(settings.public_feed_requests_allowed and db.get(GatheringSettings, 1).enabled and source and source.enabled
                and source.catalog_key in CATALOG and any(domain["enabled"] for domain in _domains(db, source.domain_ids)))


def _queue(db, source, actor_id, trigger):
    if source.active_run_id:
        active = db.get(GatheringRun, source.active_run_id)
        if active and active.status in {"QUEUED", "RUNNING"}:
            return active
        source.active_run_id = None
    now = _now()
    catalog = CATALOG[source.catalog_key]
    snapshot = {**catalog, "catalog_key": source.catalog_key, "source_id": source.id,
                "source_revision": source.revision, "domains": [domain for domain in _domains(db, source.domain_ids) if domain["enabled"]],
                "settings_revision": db.get(GatheringSettings, 1).revision}
    row = GatheringRun(id=uuid.uuid4().hex, source_id=source.id, trigger=trigger, status="QUEUED", requested_by=actor_id,
                       created_at=now, snapshot=snapshot, counts={}, result_metadata={})
    db.add(row)
    source.active_run_id = row.id
    source.next_due_at = (datetime.fromisoformat(now) + timedelta(minutes=source.interval_minutes)).isoformat()
    _audit(db, actor_id, "COLLECTION_QUEUED", row.id, {"source_id": source.id, "trigger": trigger})
    return row


def queue_collection(db, actor_id, source_id, trigger="MANUAL"):
    _owner(actor_id)
    with _locked(db):
        source = db.get(GatheringSource, source_id)
        if source is None:
            raise ApiError(404, "SOURCE_NOT_FOUND", "Research source not found.")
        if not _can_collect(db, source):
            raise ApiError(409, "COLLECTION_DISABLED", "Enable collection, this source and at least one assigned research domain. The process must also permit public feed requests.")
        if not source.active_run_id and source.last_checked_at and utcnow() - datetime.fromisoformat(source.last_checked_at) < timedelta(seconds=60):
            raise ApiError(429, "COLLECTION_COOLDOWN", "Wait at least one minute between manual requests to the same publisher.")
        return run_view(_queue(db, source, actor_id, trigger))


def queue_due(db):
    with _locked(db):
        if not settings.public_feed_requests_allowed or not db.get(GatheringSettings, 1).enabled:
            return []
        due = []
        now = _now()
        for source in db.scalars(select(GatheringSource).where(GatheringSource.enabled.is_(True))):
            if _can_collect(db, source) and not source.active_run_id and (not source.next_due_at or source.next_due_at <= now):
                due.append(_queue(db, source, "system", "SCHEDULED").id)
        return due


def _close_run(db, row, status, error=None):
    row.status, row.error, row.completed_at = status, error, _now()
    source = db.get(GatheringSource, row.source_id)
    if source.active_run_id == row.id:
        source.active_run_id = None
    if error:
        source.last_error = error


def claim_collection(db, run_id):
    with _locked(db):
        row = db.get(GatheringRun, run_id)
        if row is None or row.status != "QUEUED":
            return None
        source = db.get(GatheringSource, row.source_id)
        if not _can_collect(db, source):
            _close_run(db, row, "CANCELLED", "Collection was disabled or no assigned research domains remain active.")
            return None
        row.status, row.started_at = "RUNNING", _now()
        source.last_checked_at = row.started_at
        return dict(row.snapshot)


def fail_collection(db, run_id, message="FETCH_FAILED"):
    safe_errors = {
        "FETCH_FAILED": "The publisher request failed. No substitute data was generated.",
        "INVALID_FEED_XML": "The publisher response could not be parsed as a supported feed.",
        "UNSUPPORTED_FEED": "The publisher response is not a supported RSS or Atom feed.",
        "UNSAFE_FEED_XML": "The publisher response contains unsupported XML declarations.",
        "FEED_XML_LIMIT": "The publisher response exceeded the XML structure limit.",
        "FEED_TOO_LARGE": "The publisher response exceeded the collection size limit.",
        "FEED_REDIRECT": "The source moved. Its catalog address needs review before collection can continue.",
        "FEED_HTTP_ERROR": "The publisher returned an unsuccessful HTTP response.",
        "FEED_ENCODING": "The publisher ignored the required uncompressed download format.",
        "FEED_TIMEOUT": "The publisher request exceeded the collection time limit.",
        "FEED_NETWORK_ERROR": "The publisher could not be reached. No substitute data was generated.",
        "UNKNOWN_FEED": "The source is no longer available in the public feed catalog.",
        "CATALOG_CHANGED": "The configured catalog endpoint changed after this run was queued.",
        "COLLECTION_DISABLED": "Collection was disabled before the request started.",
    }
    with _locked(db):
        row = db.get(GatheringRun, run_id)
        if row and row.status in {"QUEUED", "RUNNING"}:
            row.result_metadata = {"error_code": message if message in safe_errors else "FETCH_FAILED"}
            _close_run(db, row, "FAILED", safe_errors.get(message, safe_errors["FETCH_FAILED"]))


def recover_collections(db):
    with _locked(db):
        pending = []
        for row in db.scalars(select(GatheringRun).where(GatheringRun.status.in_(["QUEUED", "RUNNING"]))):
            source = db.get(GatheringSource, row.source_id)
            if row.status == "RUNNING":
                _close_run(db, row, "FAILED", "Collection was interrupted by a server restart. The next scheduled request will check for new material.")
            elif not _can_collect(db, source):
                _close_run(db, row, "CANCELLED", "Collection was disabled before the request started.")
            else:
                pending.append(row.id)
        return pending


def _canonical_url(value):
    parts = urlsplit(value)
    # RSS article links may use HTTP even when the feed itself is HTTPS. They
    # are stored as source references only, never fetched by this service.
    if parts.scheme not in {"https", "http"} or not parts.hostname or parts.username or parts.password:
        raise ValueError("Invalid publication URL")
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path or "/", parts.query, ""))


def _iso(value):
    if value is None:
        return None
    parsed = value if isinstance(value, datetime) else datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Timestamp must include timezone")
    return parsed.astimezone(timezone.utc).isoformat()


def _store_revision(db, source_id, source_kind, payload, recorded_at):
    identity = _hash({"source": source_id or "manual", "url": _canonical_url(payload["url"])})
    document = db.scalar(select(ResearchDocument).where(ResearchDocument.identity_key == identity))
    created = document is None
    if document is None:
        document = ResearchDocument(id=uuid.uuid4().hex, identity_key=identity, source_id=source_id,
                                    source_kind=source_kind, first_seen_at=recorded_at, latest_revision=0)
        db.add(document)
        db.flush()
    # An omitted optional date-only field and an explicit null are equivalent.
    # Adding date precision support must not create a false content correction.
    digest = _hash({key: value for key, value in payload.items() if key != "published_on" or value is not None})
    latest = db.scalar(select(ResearchDocumentRevision).where(ResearchDocumentRevision.document_id == document.id,
                        ResearchDocumentRevision.revision == document.latest_revision))
    if latest and latest.content_hash == digest:
        return {"document_id": document.id, "revision": latest.revision, "created": False, "changed": False}
    document.latest_revision += 1
    available_at = max(recorded_at, payload.get("published_at") or recorded_at)
    db.add(ResearchDocumentRevision(id=uuid.uuid4().hex, document_id=document.id, revision=document.latest_revision,
        recorded_at=recorded_at, available_at=available_at, content_hash=digest, payload=payload))
    db.flush()
    return {"document_id": document.id, "revision": document.latest_revision, "created": created, "changed": True}


def finish_collection(db, run_id, items, fetched_at, metadata=None):
    with _locked(db):
        row = db.get(GatheringRun, run_id)
        if row is None or row.status != "RUNNING":
            return None
        recorded_at = _now()
        snapshot = row.snapshot
        counts = {"received": len(items), "new_documents": 0, "new_revisions": 0, "unchanged": 0}
        for item in items:
            payload = {"title": item["title"], "content": item["summary"], "url": item["url"],
                "publisher": snapshot["publisher"], "published_at": _iso(item.get("published_at")),
                "published_on": None,
                "occurred_at": None, "source_updated_at": _iso(item.get("updated_at")),
                "domains": snapshot["domains"], "domain_ids": [d["id"] for d in snapshot["domains"]],
                "original": dict(item), "attribution": "Configured source coverage; relevance has not been reviewed by an analyst.", "note": "Publisher-provided feed excerpt; linked article was not fetched."}
            result = _store_revision(db, row.source_id, "RSS", payload, recorded_at)
            counts["new_documents" if result["created"] else "new_revisions" if result["changed"] else "unchanged"] += 1
        row.counts = counts
        row.result_metadata = {**(metadata or {}), "fetched_at": _iso(fetched_at), "provider_cost_eur": "0.000000", "model_calls": 0}
        _close_run(db, row, "SUCCEEDED")
        source = db.get(GatheringSource, row.source_id)
        source.last_success_at, source.last_error = recorded_at, None
        _audit(db, row.requested_by, "COLLECTION_COMPLETED", row.id, counts)
        return run_view(row)


def import_document(db, actor_id, request):
    _owner(actor_id)
    request_payload = request.model_dump(mode="json")
    if request_payload.get("published_on") is None:
        request_payload.pop("published_on", None)
    request_hash = _hash(request_payload)
    with _locked(db):
        prior = db.get(GatheringImport, request.idempotency_key)
        if prior:
            if prior.request_hash != request_hash:
                raise ApiError(409, "IMPORT_KEY_REUSED", "This import key was already used with different source material.")
            return prior.result
        domains = _domains(db, request.domain_ids)
        payload = {"title": request.title.strip(), "content": request.text, "url": request.url,
            "publisher": request.publisher.strip(), "published_at": _iso(request.published_at),
            "published_on": request.published_on.isoformat() if request.published_on else None,
            "occurred_at": _iso(request.occurred_at), "source_updated_at": None,
            "domains": domains, "domain_ids": [d["id"] for d in domains],
            "original": {"import_method": "manual", "publisher_date_supplied_by": actor_id},
            "attribution": "Domains and publication date supplied by the importer; source authenticity has not been independently verified.", "note": request.note.strip()}
        result = _store_revision(db, None, "MANUAL", payload, _now())
        db.add(GatheringImport(idempotency_key=request.idempotency_key, request_hash=request_hash, actor_id=actor_id, result=result))
        _audit(db, actor_id, "RESEARCH_SOURCE_IMPORTED", result["document_id"], {"revision": result["revision"], "changed": result["changed"]})
        return result


def _revision_view(row):
    return {"id": row.id, "document_id": row.document_id, "revision": row.revision,
            "recorded_at": row.recorded_at, "available_at": row.available_at, "content_hash": row.content_hash,
            "published_on": None, **row.payload}


def _document_view(document, revision):
    return {"id": document.id, "source_id": document.source_id, "source_kind": document.source_kind,
            "first_seen_at": document.first_seen_at, "revision": _revision_view(revision)}


def _cutoff(value):
    try:
        return _iso(value)
    except (ValueError, TypeError):
        raise ApiError(422, "INVALID_LIBRARY_TIME", "Use an ISO timestamp including its timezone.")


def list_documents(db, domain_id=None, source_id=None, q=None, date_from=None, date_to=None, known_by=None, offset=0, limit=30):
    cutoff = _cutoff(known_by) if known_by else None
    date_from, date_to = _cutoff(date_from) if date_from else None, _cutoff(date_to) if date_to else None
    if date_from and date_to and date_from > date_to:
        raise ApiError(422, "INVALID_LIBRARY_RANGE", "Publication start must not follow publication end.")
    latest = select(ResearchDocumentRevision.document_id,
                    func.max(ResearchDocumentRevision.revision).label("revision")).group_by(ResearchDocumentRevision.document_id)
    if cutoff:
        latest = latest.where(ResearchDocumentRevision.available_at <= cutoff)
    latest = latest.subquery()
    query = select(ResearchDocument, ResearchDocumentRevision).join(
        ResearchDocumentRevision, ResearchDocumentRevision.document_id == ResearchDocument.id).join(latest,
        and_(latest.c.document_id == ResearchDocumentRevision.document_id,
             latest.c.revision == ResearchDocumentRevision.revision))
    # Latest eligible revision is selected before applying content/domain filters.
    # An old matching version must not leak into a current query after a correction.
    payload = ResearchDocumentRevision.payload
    if domain_id:
        domains = func.json_each(payload["domain_ids"]).table_valued("value").alias("revision_domains")
        query = query.where(select(1).select_from(domains).where(domains.c.value == domain_id).exists())
    if source_id:
        query = query.where(ResearchDocument.source_id == source_id)
    if q:
        pattern = "%" + q.lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        query = query.where(func.lower(payload["title"].as_string() + " " + payload["content"].as_string()).like(pattern, escape="\\"))
    published_at = payload["published_at"].as_string()
    published_on = payload["published_on"].as_string()
    if date_from:
        query = query.where(or_(published_at >= date_from,
                               and_(published_at.is_(None), published_on >= date_from[:10])))
    if date_to:
        query = query.where(or_(published_at <= date_to,
                               and_(published_at.is_(None), published_on <= date_to[:10])))
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.order_by(func.coalesce(published_at, published_on, ResearchDocument.first_seen_at).desc(), ResearchDocument.id.desc()).offset(offset).limit(limit)
    return {"items": [_document_view(document, revision) for document, revision in db.execute(query)],
            "total": total, "offset": offset, "limit": limit, "known_by": cutoff}


def get_document(db, document_id, known_by=None):
    document = db.get(ResearchDocument, document_id)
    if document is None:
        raise ApiError(404, "DOCUMENT_NOT_FOUND", "Research document not found.")
    query = select(ResearchDocumentRevision).where(ResearchDocumentRevision.document_id == document_id).order_by(ResearchDocumentRevision.revision.desc())
    if known_by:
        query = query.where(ResearchDocumentRevision.available_at <= _cutoff(known_by))
    revisions = list(db.scalars(query))
    if not revisions:
        raise ApiError(404, "DOCUMENT_NOT_FOUND", "Research document was not available at this information cutoff.")
    return {"document": _document_view(document, revisions[0]), "revisions": [_revision_view(r) for r in revisions]}
