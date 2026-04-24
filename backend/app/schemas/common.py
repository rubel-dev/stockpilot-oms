from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class AppBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ErrorBody(AppBaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(AppBaseModel):
    error: ErrorBody


class PaginatedResponse(AppBaseModel, Generic[T]):
    items: list[T]
    page: int
    page_size: int
    total: int

