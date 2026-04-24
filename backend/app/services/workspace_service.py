from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.repositories.workspace_repository import WorkspaceRepository
from app.schemas.workspace import WorkspaceResponse
from app.services.auth_service import CurrentUser


class WorkspaceService:
    def __init__(self, workspace_repository: WorkspaceRepository) -> None:
        self.workspace_repository = workspace_repository

    def get_current_workspace(self, current_user: CurrentUser) -> WorkspaceResponse:
        workspace = self.workspace_repository.get_by_id(current_user.workspace_id)
        if not workspace:
            raise NotFoundError("Workspace not found.")
        return WorkspaceResponse(**workspace)

    def update_current_workspace(self, current_user: CurrentUser, *, name: str) -> WorkspaceResponse:
        if current_user.role != "owner":
            raise PermissionDeniedError("Only workspace owners can update workspace settings.")
        workspace = self.workspace_repository.update_name(current_user.workspace_id, name.strip())
        if not workspace:
            raise NotFoundError("Workspace not found.")
        return WorkspaceResponse(**workspace)

