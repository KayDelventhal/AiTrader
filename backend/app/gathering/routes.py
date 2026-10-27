from fastapi import Depends, Query

from app.gathering import service
from app.gathering.contracts import (GatheringConfig, GatheringSettingsUpdate, GatheringSettingsView,
    GatheringDomainCreate, GatheringDomainUpdate, GatheringDomainView, GatheringSourceCreate,
    GatheringSourceUpdate, GatheringSourceView, GatheringRunView, GatheringManualImport,
    GatheringImportResult, GatheringDocumentDetail, GatheringDocumentPage)


def register_routes(app, db_session, identity, submit):
    prefix = "/api/v1/gathering"

    @app.get(prefix + "/config", response_model=GatheringConfig)
    def config(auth=Depends(identity), db=Depends(db_session)):
        return service.get_config(db, auth.user_id)

    @app.put(prefix + "/settings", response_model=GatheringSettingsView)
    def settings(payload: GatheringSettingsUpdate, auth=Depends(identity), db=Depends(db_session)):
        return service.update_settings(db, auth.user_id, payload)

    @app.post(prefix + "/domains", response_model=GatheringDomainView, status_code=201)
    def create_domain(payload: GatheringDomainCreate, auth=Depends(identity), db=Depends(db_session)):
        return service.save_domain(db, auth.user_id, payload)

    @app.put(prefix + "/domains/{domain_id}", response_model=GatheringDomainView)
    def update_domain(domain_id: str, payload: GatheringDomainUpdate, auth=Depends(identity), db=Depends(db_session)):
        return service.save_domain(db, auth.user_id, payload, domain_id)

    @app.post(prefix + "/sources", response_model=GatheringSourceView, status_code=201)
    def create_source(payload: GatheringSourceCreate, auth=Depends(identity), db=Depends(db_session)):
        return service.save_source(db, auth.user_id, payload)

    @app.put(prefix + "/sources/{source_id}", response_model=GatheringSourceView)
    def update_source(source_id: str, payload: GatheringSourceUpdate, auth=Depends(identity), db=Depends(db_session)):
        return service.save_source(db, auth.user_id, payload, source_id)

    @app.post(prefix + "/sources/{source_id}/collect", response_model=GatheringRunView, status_code=202)
    def collect(source_id: str, auth=Depends(identity), db=Depends(db_session)):
        run = service.queue_collection(db, auth.user_id, source_id)
        submit(run["id"])
        return run

    @app.get(prefix + "/runs", response_model=list[GatheringRunView])
    def runs(auth=Depends(identity), db=Depends(db_session)):
        return service.list_runs(db)

    @app.get(prefix + "/documents", response_model=GatheringDocumentPage)
    def documents(domain_id: str | None = None, source_id: str | None = None,
                  q: str | None = Query(default=None, max_length=200),
                  date_from: str | None = None, date_to: str | None = None, known_by: str | None = None,
                  offset: int = Query(default=0, ge=0, le=100000), limit: int = Query(default=30, ge=1, le=100),
                  auth=Depends(identity), db=Depends(db_session)):
        return service.list_documents(db, domain_id, source_id, q, date_from, date_to, known_by, offset, limit)

    @app.get(prefix + "/documents/{document_id}", response_model=GatheringDocumentDetail)
    def document(document_id: str, known_by: str | None = None, auth=Depends(identity), db=Depends(db_session)):
        return service.get_document(db, document_id, known_by)

    @app.post(prefix + "/imports", response_model=GatheringImportResult, status_code=201)
    def manual_import(payload: GatheringManualImport, auth=Depends(identity), db=Depends(db_session)):
        return service.import_document(db, auth.user_id, payload)
