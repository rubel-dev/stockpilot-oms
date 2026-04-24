from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_current_user, get_order_service
from app.schemas.order import OrderCreateRequest, OrderDetailResponse, OrderListResponse, OrderUpdateRequest
from app.services.auth_service import CurrentUser
from app.services.order_service import OrderService

router = APIRouter()


@router.get("", response_model=OrderListResponse)
def list_orders(
    order_service: Annotated[OrderService, Depends(get_order_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    order_type: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    supplier_id: str | None = None,
    warehouse_id: str | None = None,
    search: str | None = None,
    sort: str = Query(default="updated_at"),
    direction: str = Query(default="desc"),
) -> OrderListResponse:
    return order_service.list_orders(current_user, page=page, page_size=page_size, order_type=order_type, status=status_filter, supplier_id=supplier_id, warehouse_id=warehouse_id, search=search, sort=sort, direction=direction)


@router.post("", response_model=OrderDetailResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreateRequest,
    order_service: Annotated[OrderService, Depends(get_order_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> OrderDetailResponse:
    return order_service.create_order(current_user, payload.model_dump())


@router.get("/{order_id}", response_model=OrderDetailResponse)
def get_order(
    order_id: str,
    order_service: Annotated[OrderService, Depends(get_order_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> OrderDetailResponse:
    return order_service.get_order(current_user, order_id)


@router.patch("/{order_id}", response_model=OrderDetailResponse)
def update_order(
    order_id: str,
    payload: OrderUpdateRequest,
    order_service: Annotated[OrderService, Depends(get_order_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> OrderDetailResponse:
    return order_service.update_order(current_user, order_id, payload.model_dump(exclude_unset=True))


@router.post("/{order_id}/confirm", response_model=OrderDetailResponse)
def confirm_order(
    order_id: str,
    order_service: Annotated[OrderService, Depends(get_order_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> OrderDetailResponse:
    return order_service.confirm_order(current_user, order_id)


@router.post("/{order_id}/process", response_model=OrderDetailResponse)
def process_order(
    order_id: str,
    order_service: Annotated[OrderService, Depends(get_order_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> OrderDetailResponse:
    return order_service.process_order(current_user, order_id)


@router.post("/{order_id}/ship", response_model=OrderDetailResponse)
def ship_order(
    order_id: str,
    order_service: Annotated[OrderService, Depends(get_order_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> OrderDetailResponse:
    return order_service.ship_order(current_user, order_id)


@router.post("/{order_id}/complete", response_model=OrderDetailResponse)
def complete_order(
    order_id: str,
    order_service: Annotated[OrderService, Depends(get_order_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> OrderDetailResponse:
    return order_service.complete_order(current_user, order_id)


@router.post("/{order_id}/cancel", response_model=OrderDetailResponse)
def cancel_order(
    order_id: str,
    order_service: Annotated[OrderService, Depends(get_order_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> OrderDetailResponse:
    return order_service.cancel_order(current_user, order_id)

