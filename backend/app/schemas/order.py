from datetime import datetime
from typing import Literal

from pydantic import Field, model_validator

from app.schemas.common import AppBaseModel, PaginatedResponse


class OrderItemCreateRequest(AppBaseModel):
    product_id: str
    quantity: int = Field(gt=0)
    unit_price: float | None = Field(default=None, ge=0)
    unit_cost: float | None = Field(default=None, ge=0)


class OrderCreateRequest(AppBaseModel):
    order_type: Literal["sales", "purchase"]
    warehouse_id: str
    supplier_id: str | None = None
    customer_name: str | None = Field(default=None, max_length=150)
    notes: str | None = Field(default=None, max_length=1000)
    items: list[OrderItemCreateRequest]

    @model_validator(mode="after")
    def validate_order_party(self):
        if self.order_type == "sales" and not self.customer_name:
            raise ValueError("Sales orders require customer_name.")
        if self.order_type == "purchase" and not self.supplier_id:
            raise ValueError("Purchase orders require supplier_id.")
        if not self.items:
            raise ValueError("At least one order item is required.")
        return self


class OrderUpdateRequest(AppBaseModel):
    supplier_id: str | None = None
    customer_name: str | None = Field(default=None, max_length=150)
    notes: str | None = Field(default=None, max_length=1000)
    items: list[OrderItemCreateRequest] | None = None


class OrderItemResponse(AppBaseModel):
    id: str
    product_id: str
    product_name: str
    product_sku: str
    quantity: int
    unit_price: float | None = None
    unit_cost: float | None = None
    line_total: float
    created_at: datetime
    updated_at: datetime


class OrderListItem(AppBaseModel):
    id: str
    workspace_id: str
    order_number: str
    order_type: str
    status: str
    warehouse_id: str
    warehouse_name: str
    supplier_id: str | None = None
    supplier_name: str | None = None
    customer_name: str | None = None
    item_count: int
    subtotal_amount: float
    created_at: datetime
    updated_at: datetime


class OrderListResponse(PaginatedResponse[OrderListItem]):
    pass


class OrderDetailResponse(AppBaseModel):
    id: str
    workspace_id: str
    order_number: str
    order_type: str
    status: str
    warehouse_id: str
    warehouse_name: str
    supplier_id: str | None = None
    supplier_name: str | None = None
    customer_name: str | None = None
    notes: str | None = None
    subtotal_amount: float
    created_by: str | None = None
    confirmed_at: datetime | None = None
    processed_at: datetime | None = None
    shipped_at: datetime | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemResponse]

