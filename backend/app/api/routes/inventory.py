from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_current_user, get_inventory_service
from app.schemas.inventory import (
    InventoryBalanceListResponse,
    InventoryMovementListResponse,
    InventoryMovementResponse,
    StockAdjustmentRequest,
    StockInRequest,
    StockOutRequest,
    StockTransferRequest,
)
from app.services.auth_service import CurrentUser
from app.services.inventory_service import InventoryService

router = APIRouter()


@router.get("", response_model=InventoryBalanceListResponse)
def list_balances(
    inventory_service: Annotated[InventoryService, Depends(get_inventory_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    product_id: str | None = None,
    warehouse_id: str | None = None,
    low_stock: bool | None = None,
    search: str | None = None,
) -> InventoryBalanceListResponse:
    return inventory_service.list_balances(
        current_user,
        page=page,
        page_size=page_size,
        product_id=product_id,
        warehouse_id=warehouse_id,
        low_stock=low_stock,
        search=search,
    )


@router.get("/movements", response_model=InventoryMovementListResponse)
def list_movements(
    inventory_service: Annotated[InventoryService, Depends(get_inventory_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    product_id: str | None = None,
    warehouse_id: str | None = None,
    movement_type: str | None = None,
    search: str | None = None,
) -> InventoryMovementListResponse:
    return inventory_service.list_movements(
        current_user,
        page=page,
        page_size=page_size,
        product_id=product_id,
        warehouse_id=warehouse_id,
        movement_type=movement_type,
        search=search,
    )


@router.post("/movements/stock-in", response_model=InventoryMovementResponse, status_code=status.HTTP_201_CREATED)
def stock_in(
    payload: StockInRequest,
    inventory_service: Annotated[InventoryService, Depends(get_inventory_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> InventoryMovementResponse:
    return inventory_service.stock_in(current_user, payload.model_dump())


@router.post("/movements/stock-out", response_model=InventoryMovementResponse, status_code=status.HTTP_201_CREATED)
def stock_out(
    payload: StockOutRequest,
    inventory_service: Annotated[InventoryService, Depends(get_inventory_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> InventoryMovementResponse:
    return inventory_service.stock_out(current_user, payload.model_dump())


@router.post("/movements/transfer", response_model=list[InventoryMovementResponse], status_code=status.HTTP_201_CREATED)
def transfer(
    payload: StockTransferRequest,
    inventory_service: Annotated[InventoryService, Depends(get_inventory_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> list[InventoryMovementResponse]:
    return inventory_service.transfer(current_user, payload.model_dump())


@router.post("/movements/adjustment", response_model=InventoryMovementResponse, status_code=status.HTTP_201_CREATED)
def adjust_stock(
    payload: StockAdjustmentRequest,
    inventory_service: Annotated[InventoryService, Depends(get_inventory_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> InventoryMovementResponse:
    return inventory_service.adjust_stock(current_user, payload.model_dump())

