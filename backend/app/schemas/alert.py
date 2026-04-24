from datetime import datetime

from app.schemas.common import AppBaseModel, PaginatedResponse


class AlertResponse(AppBaseModel):
    id: str
    workspace_id: str
    alert_type: str
    severity: str
    status: str
    product_id: str | None = None
    warehouse_id: str | None = None
    order_id: str | None = None
    title: str
    message: str
    metadata: dict
    resolved_by: str | None = None
    resolved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class AlertListResponse(PaginatedResponse[AlertResponse]):
    pass


class AlertSummaryItem(AppBaseModel):
    alert_type: str
    severity: str
    status: str
    count: int


class AlertSummaryResponse(AppBaseModel):
    items: list[AlertSummaryItem]

