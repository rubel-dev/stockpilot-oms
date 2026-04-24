from datetime import datetime

from pydantic import EmailStr, Field

from app.schemas.common import AppBaseModel, PaginatedResponse


class SupplierCreateRequest(AppBaseModel):
    name: str = Field(min_length=2, max_length=150)
    contact_name: str | None = Field(default=None, max_length=120)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, max_length=1000)


class SupplierUpdateRequest(AppBaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    contact_name: str | None = Field(default=None, max_length=120)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = Field(default=None, max_length=500)
    status: str | None = None
    notes: str | None = Field(default=None, max_length=1000)


class SupplierProductLinkRequest(AppBaseModel):
    product_id: str
    supplier_sku: str | None = Field(default=None, max_length=80)
    lead_time_days: int | None = Field(default=None, ge=0)
    minimum_order_quantity: int = Field(default=0, ge=0)
    unit_cost: float | None = Field(default=None, ge=0)
    is_preferred: bool = False


class SupplierListItem(AppBaseModel):
    id: str
    workspace_id: str
    name: str
    contact_name: str | None = None
    email: str | None = None
    phone: str | None = None
    status: str
    active_product_count: int
    last_restock_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class SupplierListResponse(PaginatedResponse[SupplierListItem]):
    pass


class SupplierProductLink(AppBaseModel):
    id: str
    product_id: str
    product_name: str
    product_sku: str
    supplier_sku: str | None = None
    lead_time_days: int | None = None
    minimum_order_quantity: int
    unit_cost: float | None = None
    is_preferred: bool
    created_at: datetime
    updated_at: datetime


class SupplierDetailResponse(AppBaseModel):
    id: str
    workspace_id: str
    name: str
    contact_name: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    status: str
    notes: str | None = None
    active_product_count: int
    last_restock_at: datetime | None = None
    linked_products: list[SupplierProductLink]
    created_at: datetime
    updated_at: datetime

