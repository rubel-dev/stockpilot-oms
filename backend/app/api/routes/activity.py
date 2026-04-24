from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_activity_service, get_current_user
from app.schemas.activity import ActivityLogListResponse
from app.services.activity_service import ActivityService
from app.services.auth_service import CurrentUser

router = APIRouter()


@router.get("", response_model=ActivityLogListResponse)
def list_activity(
    activity_service: Annotated[ActivityService, Depends(get_activity_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    actor_user_id: str | None = None,
    entity_type: str | None = None,
    action: str | None = None,
    search: str | None = None,
) -> ActivityLogListResponse:
    return activity_service.list_logs(current_user, page=page, page_size=page_size, actor_user_id=actor_user_id, entity_type=entity_type, action=action, search=search)

