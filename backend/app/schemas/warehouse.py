from datetime import datetime

from pydantic import Field

from app.schemas.common import AppBaseModel, PaginatedResponse


class WarehouseCreateRequest(AppBaseModel):
    name: str = Field(min_length=2, max_length=120)
    code: str = Field(min_length=2, max_length=50)
    address_line1: str | None = Field(default=None, max_length=200)
    address_line2: str | None = Field(default=None, max_length=200)
    city: str | None = Field(default=None, max_length=100)
    state_region: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=30)
    country: str | None = Field(default=None, max_length=100)


class WarehouseUpdateRequest(AppBaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    code: str | None = Field(default=None, min_length=2, max_length=50)
    address_line1: str | None = Field(default=None, max_length=200)
    address_line2: str | None = Field(default=None, max_length=200)
    city: str | None = Field(default=None, max_length=100)
    state_region: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=30)
    country: str | None = Field(default=None, max_length=100)
    status: str | None = None


class WarehouseListItem(AppBaseModel):
    id: str
    workspace_id: str
    name: str
    code: str
    city: str | None = None
    country: str | None = None
    status: str
    total_skus: int
    total_units: int
    total_reserved: int
    low_stock_items: int
    created_at: datetime
    updated_at: datetime


class WarehouseListResponse(PaginatedResponse[WarehouseListItem]):
    pass


class WarehouseDetailResponse(AppBaseModel):
    id: str
    workspace_id: str
    name: str
    code: str
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state_region: str | None = None
    postal_code: str | None = None
    country: str | None = None
    status: str
    total_skus: int
    total_units: int
    total_reserved: int
    low_stock_items: int
    created_at: datetime
    updated_at: datetime

