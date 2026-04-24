from datetime import datetime

from pydantic import Field

from app.schemas.common import AppBaseModel, PaginatedResponse


class StockInRequest(AppBaseModel):
    product_id: str
    warehouse_id: str
    quantity: int = Field(gt=0)
    reason: str = Field(min_length=2, max_length=120)
    reference_type: str | None = Field(default="manual", max_length=50)
    reference_id: str | None = None
    notes: str | None = Field(default=None, max_length=500)


class StockOutRequest(AppBaseModel):
    product_id: str
    warehouse_id: str
    quantity: int = Field(gt=0)
    reason: str = Field(min_length=2, max_length=120)
    reference_type: str | None = Field(default="manual", max_length=50)
    reference_id: str | None = None
    notes: str | None = Field(default=None, max_length=500)


class StockTransferRequest(AppBaseModel):
    product_id: str
    source_warehouse_id: str
    destination_warehouse_id: str
    quantity: int = Field(gt=0)
    reason: str = Field(min_length=2, max_length=120)
    notes: str | None = Field(default=None, max_length=500)


class StockAdjustmentRequest(AppBaseModel):
    product_id: str
    warehouse_id: str
    counted_quantity: int = Field(ge=0)
    reason: str = Field(min_length=2, max_length=120)
    notes: str | None = Field(default=None, max_length=500)


class InventoryBalanceItem(AppBaseModel):
    product_id: str
    product_name: str
    product_sku: str
    warehouse_id: str
    warehouse_name: str
    warehouse_code: str
    reorder_point: int
    on_hand_quantity: int
    reserved_quantity: int
    available_quantity: int
    updated_at: datetime


class InventoryBalanceListResponse(PaginatedResponse[InventoryBalanceItem]):
    pass


class InventoryMovementResponse(AppBaseModel):
    id: str
    workspace_id: str
    product_id: str
    product_name: str
    product_sku: str
    warehouse_id: str
    warehouse_name: str
    destination_warehouse_id: str | None = None
    destination_warehouse_name: str | None = None
    movement_type: str
    quantity: int
    quantity_before: int
    quantity_after: int
    reason: str | None = None
    reference_type: str | None = None
    reference_id: str | None = None
    notes: str | None = None
    created_by: str | None = None
    created_by_name: str | None = None
    created_at: datetime


class InventoryMovementListResponse(PaginatedResponse[InventoryMovementResponse]):
    pass

