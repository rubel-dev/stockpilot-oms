from fastapi import APIRouter

from app.api.routes import activity, alerts, analytics, auth, inventory, orders, products, suppliers, warehouses, workspaces

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(workspaces.router, prefix="/workspaces", tags=["workspaces"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(warehouses.router, prefix="/warehouses", tags=["warehouses"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["inventory"])
api_router.include_router(suppliers.router, prefix="/suppliers", tags=["suppliers"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(activity.router, prefix="/activity", tags=["activity"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
