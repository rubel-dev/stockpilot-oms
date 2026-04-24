from app.core.pagination import normalize_pagination
from app.repositories.activity_repository import ActivityRepository
from app.schemas.activity import ActivityLogListResponse
from app.services.auth_service import CurrentUser


class ActivityService:
    def __init__(self, activity_repository: ActivityRepository) -> None:
        self.activity_repository = activity_repository

    def list_logs(
        self,
        current_user: CurrentUser,
        *,
        page: int,
        page_size: int,
        actor_user_id: str | None,
        entity_type: str | None,
        action: str | None,
        search: str | None,
    ) -> ActivityLogListResponse:
        pagination = normalize_pagination(page, page_size)
        items = self.activity_repository.list_logs(
            workspace_id=current_user.workspace_id,
            page_size=pagination.page_size,
            offset=pagination.offset,
            actor_user_id=actor_user_id,
            entity_type=entity_type,
            action=action,
            search=search.strip() if search else None,
        )
        total = self.activity_repository.count_logs(
            workspace_id=current_user.workspace_id,
            actor_user_id=actor_user_id,
            entity_type=entity_type,
            action=action,
            search=search.strip() if search else None,
        )
        return ActivityLogListResponse(items=items, page=pagination.page, page_size=pagination.page_size, total=total)

