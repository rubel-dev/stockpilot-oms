from datetime import datetime

from pydantic import Field

from app.schemas.common import AppBaseModel


class WorkspaceResponse(AppBaseModel):
    id: str
    name: str
    slug: str
    created_at: datetime
    updated_at: datetime


class WorkspaceUpdateRequest(AppBaseModel):
    name: str = Field(min_length=2, max_length=120)

