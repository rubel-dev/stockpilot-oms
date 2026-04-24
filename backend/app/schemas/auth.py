from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import AppBaseModel


class RegisterRequest(AppBaseModel):
    workspace_name: str = Field(min_length=2, max_length=120)
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(AppBaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class AuthUser(AppBaseModel):
    id: str
    workspace_id: str
    name: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime | None = None


class WorkspaceSummary(AppBaseModel):
    id: str
    name: str
    slug: str


class TokenResponse(AppBaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthUser


class CurrentUserResponse(AppBaseModel):
    user: AuthUser
    workspace: WorkspaceSummary


class TokenPayload(BaseModel):
    sub: str
    workspace_id: str
    role: str

