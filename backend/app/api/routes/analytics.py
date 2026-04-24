from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_analytics_service, get_current_user
from app.schemas.analytics import (
    AnalyticsOverviewResponse,
    MonthlyOrderTrendResponse,
    StockByWarehouseResponse,
    SupplierRestockSummaryResponse,
    TopMovingProductsResponse,
)
from app.services.analytics_service import AnalyticsService
from app.services.auth_service import CurrentUser

router = APIRouter()


@router.get("/overview", response_model=AnalyticsOverviewResponse)
def overview(
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> AnalyticsOverviewResponse:
    return analytics_service.overview(current_user)


@router.get("/stock-by-warehouse", response_model=StockByWarehouseResponse)
def stock_by_warehouse(
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> StockByWarehouseResponse:
    return analytics_service.stock_by_warehouse(current_user)


@router.get("/top-moving-products", response_model=TopMovingProductsResponse)
def top_moving_products(
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    limit: int = Query(default=10, ge=1, le=100),
) -> TopMovingProductsResponse:
    return analytics_service.top_moving_products(current_user, limit=limit)


@router.get("/monthly-orders", response_model=MonthlyOrderTrendResponse)
def monthly_orders(
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> MonthlyOrderTrendResponse:
    return analytics_service.monthly_order_trends(current_user)


@router.get("/supplier-restocks", response_model=SupplierRestockSummaryResponse)
def supplier_restocks(
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> SupplierRestockSummaryResponse:
    return analytics_service.supplier_restock_summaries(current_user)

