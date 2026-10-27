from fastapi import Depends
from app.workspace import service
from app.workspace.contracts import (WorkspaceSettingsView, WorkspaceSettingsUpdate, CostSummary,
    ManualCost, ReserveCost, ReconcileCost, CostEntryView, RecurringCostCreate, RecurringCostView, StopRecurringCost)


def register_routes(app, db_session, identity):
    prefix = "/api/v1"

    @app.get(prefix + "/workspace/settings", response_model=WorkspaceSettingsView)
    def workspace_settings(auth=Depends(identity), db=Depends(db_session)):
        return service.get_settings(db, auth.user_id)

    @app.put(prefix + "/workspace/settings", response_model=WorkspaceSettingsView)
    def update_settings(payload: WorkspaceSettingsUpdate, auth=Depends(identity), db=Depends(db_session)):
        return service.update_settings(db, auth.user_id, payload)

    @app.get(prefix + "/costs", response_model=CostSummary)
    def costs(month: str | None = None, auth=Depends(identity), db=Depends(db_session)):
        return service.cost_summary(db, month, auth.user_id)

    @app.post(prefix + "/costs/entries", response_model=CostEntryView, status_code=201)
    def record_cost(payload: ManualCost, auth=Depends(identity), db=Depends(db_session)):
        return service.record_cost(db, auth.user_id, payload)

    @app.post(prefix + "/costs/reservations", response_model=CostEntryView, status_code=201)
    def reserve_cost(payload: ReserveCost, auth=Depends(identity), db=Depends(db_session)):
        return service.reserve_cost(db, auth.user_id, payload)

    @app.post(prefix + "/costs/{entry_id}/reconcile", response_model=CostEntryView)
    def reconcile_cost(entry_id: str, payload: ReconcileCost, auth=Depends(identity), db=Depends(db_session)):
        return service.reconcile_cost(db, auth.user_id, entry_id, payload)

    @app.post(prefix + "/costs/recurring", response_model=RecurringCostView, status_code=201)
    def recurring_cost(payload: RecurringCostCreate, auth=Depends(identity), db=Depends(db_session)):
        return service.create_recurring(db, auth.user_id, payload)

    @app.post(prefix + "/costs/recurring/{recurring_id}/stop", response_model=RecurringCostView)
    def stop_recurring(recurring_id: str, payload: StopRecurringCost, auth=Depends(identity), db=Depends(db_session)):
        return service.stop_recurring(db, auth.user_id, recurring_id, payload)
