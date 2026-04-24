from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_alert_service, get_current_user
from app.schemas.alert import AlertListResponse, AlertResponse, AlertSummaryResponse
from app.services.alert_service import AlertService
from app.services.auth_service import CurrentUser

router = APIRouter()


@router.get("", response_model=AlertListResponse)
def list_alerts(
    alert_service: Annotated[AlertService, Depends(get_alert_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    alert_type: str | None = None,
    severity: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    warehouse_id: str | None = None,
    product_id: str | None = None,
) -> AlertListResponse:
    return alert_service.list_alerts(current_user, page=page, page_size=page_size, alert_type=alert_type, severity=severity, status=status_filter, warehouse_id=warehouse_id, product_id=product_id)


@router.get("/summary", response_model=AlertSummaryResponse)
def alert_summary(
    alert_service: Annotated[AlertService, Depends(get_alert_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> AlertSummaryResponse:
    return alert_service.summary(current_user)


@router.post("/recalculate", response_model=AlertSummaryResponse)
def recalculate_alerts(
    alert_service: Annotated[AlertService, Depends(get_alert_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> AlertSummaryResponse:
    return alert_service.recalculate(current_user)


@router.post("/{alert_id}/resolve", response_model=AlertResponse)
def resolve_alert(
    alert_id: str,
    alert_service: Annotated[AlertService, Depends(get_alert_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> AlertResponse:
    return AlertResponse(**alert_service.resolve(current_user, alert_id))


@router.post("/{alert_id}/dismiss", response_model=AlertResponse)
def dismiss_alert(
    alert_id: str,
    alert_service: Annotated[AlertService, Depends(get_alert_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> AlertResponse:
    return AlertResponse(**alert_service.dismiss(current_user, alert_id))

