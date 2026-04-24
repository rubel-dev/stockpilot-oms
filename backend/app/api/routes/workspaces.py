from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_workspace_service
from app.schemas.workspace import WorkspaceResponse, WorkspaceUpdateRequest
from app.services.auth_service import CurrentUser
from app.services.workspace_service import WorkspaceService

router = APIRouter()


@router.get("/current", response_model=WorkspaceResponse)
def get_current_workspace(
    workspace_service: Annotated[WorkspaceService, Depends(get_workspace_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> WorkspaceResponse:
    return workspace_service.get_current_workspace(current_user)


@router.patch("/current", response_model=WorkspaceResponse)
def update_current_workspace(
    payload: WorkspaceUpdateRequest,
    workspace_service: Annotated[WorkspaceService, Depends(get_workspace_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> WorkspaceResponse:
    return workspace_service.update_current_workspace(current_user, name=payload.name)

