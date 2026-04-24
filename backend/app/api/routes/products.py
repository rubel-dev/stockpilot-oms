from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_current_user, get_product_service
from app.schemas.product import (
    ProductCreateRequest,
    ProductDetailResponse,
    ProductListResponse,
    ProductUpdateRequest,
)
from app.services.auth_service import CurrentUser
from app.services.product_service import ProductService

router = APIRouter()


@router.get("", response_model=ProductListResponse)
def list_products(
    product_service: Annotated[ProductService, Depends(get_product_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    search: str | None = None,
    category_id: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    sort: str = Query(default="updated_at"),
    direction: str = Query(default="desc"),
) -> ProductListResponse:
    return product_service.list_products(
        current_user,
        page=page,
        page_size=page_size,
        search=search,
        category_id=category_id,
        status=status_filter,
        sort=sort,
        direction=direction,
    )


@router.post("", response_model=ProductDetailResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreateRequest,
    product_service: Annotated[ProductService, Depends(get_product_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> ProductDetailResponse:
    return product_service.create_product(current_user, payload.model_dump())


@router.get("/{product_id}", response_model=ProductDetailResponse)
def get_product(
    product_id: str,
    product_service: Annotated[ProductService, Depends(get_product_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> ProductDetailResponse:
    return product_service.get_product(current_user, product_id)


@router.patch("/{product_id}", response_model=ProductDetailResponse)
def update_product(
    product_id: str,
    payload: ProductUpdateRequest,
    product_service: Annotated[ProductService, Depends(get_product_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> ProductDetailResponse:
    return product_service.update_product(current_user, product_id, payload.model_dump(exclude_unset=True))


@router.post("/{product_id}/archive", response_model=ProductDetailResponse)
def archive_product(
    product_id: str,
    product_service: Annotated[ProductService, Depends(get_product_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> ProductDetailResponse:
    return product_service.archive_product(current_user, product_id)

