from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.analytics import (
    AnalyticsOverviewResponse,
    MonthlyOrderTrendResponse,
    StockByWarehouseResponse,
    SupplierRestockSummaryResponse,
    TopMovingProductsResponse,
)
from app.services.auth_service import CurrentUser


class AnalyticsService:
    def __init__(self, analytics_repository: AnalyticsRepository) -> None:
        self.analytics_repository = analytics_repository

    def overview(self, current_user: CurrentUser) -> AnalyticsOverviewResponse:
        return AnalyticsOverviewResponse(items=self.analytics_repository.overview(current_user.workspace_id))

    def stock_by_warehouse(self, current_user: CurrentUser) -> StockByWarehouseResponse:
        return StockByWarehouseResponse(items=self.analytics_repository.stock_by_warehouse(current_user.workspace_id))

    def top_moving_products(self, current_user: CurrentUser, *, limit: int) -> TopMovingProductsResponse:
        return TopMovingProductsResponse(items=self.analytics_repository.top_moving_products(current_user.workspace_id, limit))

    def monthly_order_trends(self, current_user: CurrentUser) -> MonthlyOrderTrendResponse:
        return MonthlyOrderTrendResponse(items=self.analytics_repository.monthly_order_trends(current_user.workspace_id))

    def supplier_restock_summaries(self, current_user: CurrentUser) -> SupplierRestockSummaryResponse:
        return SupplierRestockSummaryResponse(items=self.analytics_repository.supplier_restock_summaries(current_user.workspace_id))

