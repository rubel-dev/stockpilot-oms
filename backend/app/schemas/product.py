from datetime import datetime

from pydantic import Field

from app.schemas.common import AppBaseModel, PaginatedResponse


class ProductCreateRequest(AppBaseModel):
    name: str = Field(min_length=2, max_length=150)
    sku: str | None = Field(default=None, max_length=80)
    category_id: str | None = None
    description: str | None = Field(default=None, max_length=1000)
    unit: str = Field(default="each", min_length=1, max_length=30)
    reorder_point: int = Field(default=0, ge=0)
    reorder_quantity: int = Field(default=0, ge=0)


class ProductUpdateRequest(AppBaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    sku: str | None = Field(default=None, max_length=80)
    category_id: str | None = None
    description: str | None = Field(default=None, max_length=1000)
    unit: str | None = Field(default=None, min_length=1, max_length=30)
    reorder_point: int | None = Field(default=None, ge=0)
    reorder_quantity: int | None = Field(default=None, ge=0)
    status: str | None = None


class ProductListItem(AppBaseModel):
    id: str
    workspace_id: str
    category_id: str | None = None
    category_name: str | None = None
    name: str
    sku: str
    unit: str
    reorder_point: int
    reorder_quantity: int
    status: str
    total_on_hand: int
    total_reserved: int
    total_available: int
    warehouse_count: int
    created_at: datetime
    updated_at: datetime


class ProductListResponse(PaginatedResponse[ProductListItem]):
    pass


class ProductDetailResponse(AppBaseModel):
    id: str
    workspace_id: str
    category_id: str | None = None
    category_name: str | None = None
    name: str
    sku: str
    description: str | None = None
    unit: str
    reorder_point: int
    reorder_quantity: int
    status: str
    total_on_hand: int
    total_reserved: int
    total_available: int
    warehouse_count: int
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime

