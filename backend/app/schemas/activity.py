from datetime import datetime

from app.schemas.common import AppBaseModel, PaginatedResponse


class ActivityLogResponse(AppBaseModel):
    id: str
    workspace_id: str
    actor_user_id: str | None = None
    actor_name: str | None = None
    action: str
    entity_type: str
    entity_id: str | None = None
    summary: str
    metadata: dict
    created_at: datetime


class ActivityLogListResponse(PaginatedResponse[ActivityLogResponse]):
    pass

