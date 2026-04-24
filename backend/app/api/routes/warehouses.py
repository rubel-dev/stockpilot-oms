from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_current_user, get_warehouse_service
from app.schemas.warehouse import (
    WarehouseCreateRequest,
    WarehouseDetailResponse,
    WarehouseListResponse,
    WarehouseUpdateRequest,
)
from app.services.auth_service import CurrentUser
from app.services.warehouse_service import WarehouseService

router = APIRouter()


@router.get("", response_model=WarehouseListResponse)
def list_warehouses(
    warehouse_service: Annotated[WarehouseService, Depends(get_warehouse_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    search: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    sort: str = Query(default="updated_at"),
    direction: str = Query(default="desc"),
) -> WarehouseListResponse:
    return warehouse_service.list_warehouses(
        current_user,
        page=page,
        page_size=page_size,
        search=search,
        status=status_filter,
        sort=sort,
        direction=direction,
    )


@router.post("", response_model=WarehouseDetailResponse, status_code=status.HTTP_201_CREATED)
def create_warehouse(
    payload: WarehouseCreateRequest,
    warehouse_service: Annotated[WarehouseService, Depends(get_warehouse_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> WarehouseDetailResponse:
    return warehouse_service.create_warehouse(current_user, payload.model_dump())


@router.get("/{warehouse_id}", response_model=WarehouseDetailResponse)
def get_warehouse(
    warehouse_id: str,
    warehouse_service: Annotated[WarehouseService, Depends(get_warehouse_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> WarehouseDetailResponse:
    return warehouse_service.get_warehouse(current_user, warehouse_id)


@router.patch("/{warehouse_id}", response_model=WarehouseDetailResponse)
def update_warehouse(
    warehouse_id: str,
    payload: WarehouseUpdateRequest,
    warehouse_service: Annotated[WarehouseService, Depends(get_warehouse_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> WarehouseDetailResponse:
    return warehouse_service.update_warehouse(
        current_user,
        warehouse_id,
        payload.model_dump(exclude_unset=True),
    )

