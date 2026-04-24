from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.deps import get_current_user, get_supplier_service
from app.schemas.supplier import (
    SupplierCreateRequest,
    SupplierDetailResponse,
    SupplierListResponse,
    SupplierProductLinkRequest,
    SupplierUpdateRequest,
)
from app.services.auth_service import CurrentUser
from app.services.supplier_service import SupplierService

router = APIRouter()


@router.get("", response_model=SupplierListResponse)
def list_suppliers(
    supplier_service: Annotated[SupplierService, Depends(get_supplier_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    search: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    sort: str = Query(default="updated_at"),
    direction: str = Query(default="desc"),
) -> SupplierListResponse:
    return supplier_service.list_suppliers(current_user, page=page, page_size=page_size, search=search, status=status_filter, sort=sort, direction=direction)


@router.post("", response_model=SupplierDetailResponse, status_code=status.HTTP_201_CREATED)
def create_supplier(
    payload: SupplierCreateRequest,
    supplier_service: Annotated[SupplierService, Depends(get_supplier_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> SupplierDetailResponse:
    return supplier_service.create_supplier(current_user, payload.model_dump())


@router.get("/{supplier_id}", response_model=SupplierDetailResponse)
def get_supplier(
    supplier_id: str,
    supplier_service: Annotated[SupplierService, Depends(get_supplier_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> SupplierDetailResponse:
    return supplier_service.get_supplier(current_user, supplier_id)


@router.patch("/{supplier_id}", response_model=SupplierDetailResponse)
def update_supplier(
    supplier_id: str,
    payload: SupplierUpdateRequest,
    supplier_service: Annotated[SupplierService, Depends(get_supplier_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> SupplierDetailResponse:
    return supplier_service.update_supplier(current_user, supplier_id, payload.model_dump(exclude_unset=True))


@router.post("/{supplier_id}/products", response_model=SupplierDetailResponse)
def link_product(
    supplier_id: str,
    payload: SupplierProductLinkRequest,
    supplier_service: Annotated[SupplierService, Depends(get_supplier_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> SupplierDetailResponse:
    return supplier_service.link_product(current_user, supplier_id, payload.model_dump())


@router.delete("/{supplier_id}/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def unlink_product(
    supplier_id: str,
    product_id: str,
    supplier_service: Annotated[SupplierService, Depends(get_supplier_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> Response:
    supplier_service.unlink_product(current_user, supplier_id, product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

