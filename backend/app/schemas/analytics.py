from app.schemas.common import AppBaseModel


class AnalyticsMetric(AppBaseModel):
    key: str
    value: int | float


class AnalyticsOverviewResponse(AppBaseModel):
    items: list[AnalyticsMetric]


class StockByWarehouseItem(AppBaseModel):
    warehouse_id: str
    warehouse_name: str
    warehouse_code: str
    sku_count: int
    total_on_hand: int
    total_reserved: int
    total_available: int


class StockByWarehouseResponse(AppBaseModel):
    items: list[StockByWarehouseItem]


class TopMovingProductItem(AppBaseModel):
    product_id: str
    product_name: str
    product_sku: str
    total_moved: int
    movement_count: int


class TopMovingProductsResponse(AppBaseModel):
    items: list[TopMovingProductItem]


class MonthlyOrderTrendItem(AppBaseModel):
    month_bucket: str
    order_type: str
    order_count: int
    gross_amount: float


class MonthlyOrderTrendResponse(AppBaseModel):
    items: list[MonthlyOrderTrendItem]


class SupplierRestockSummaryItem(AppBaseModel):
    supplier_id: str
    supplier_name: str
    purchase_order_count: int
    unique_products: int
    total_units_ordered: int
    total_spend: float


class SupplierRestockSummaryResponse(AppBaseModel):
    items: list[SupplierRestockSummaryItem]

