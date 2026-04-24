from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from psycopg import Connection

from app.core.config import Settings, get_settings
from app.core.security import decode_access_token
from app.db.connection import Database
from app.db.session import get_connection
from app.repositories.auth_repository import AuthRepository
from app.repositories.activity_repository import ActivityRepository
from app.repositories.alert_repository import AlertRepository
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.supplier_repository import SupplierRepository
from app.repositories.warehouse_repository import WarehouseRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.schemas.auth import TokenPayload
from app.services.activity_service import ActivityService
from app.services.alert_service import AlertService
from app.services.analytics_service import AnalyticsService
from app.services.auth_service import AuthService, CurrentUser
from app.services.inventory_service import InventoryService
from app.services.order_service import OrderService
from app.services.product_service import ProductService
from app.services.supplier_service import SupplierService
from app.services.warehouse_service import WarehouseService
from app.services.workspace_service import WorkspaceService

bearer_scheme = HTTPBearer(auto_error=False)


def get_database(settings: Annotated[Settings, Depends(get_settings)]) -> Database:
    if not hasattr(get_database, "_database"):
        get_database._database = Database(settings)  # type: ignore[attr-defined]
    return get_database._database  # type: ignore[attr-defined]


def get_db_connection(
    database: Annotated[Database, Depends(get_database)],
):
    yield from get_connection(database)


def get_auth_service(
    connection: Annotated[Connection, Depends(get_db_connection)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthService:
    return AuthService(
        auth_repository=AuthRepository(connection),
        workspace_repository=WorkspaceRepository(connection),
        settings=settings,
    )


def get_workspace_service(
    connection: Annotated[Connection, Depends(get_db_connection)],
) -> WorkspaceService:
    return WorkspaceService(WorkspaceRepository(connection))


def get_product_service(
    connection: Annotated[Connection, Depends(get_db_connection)],
) -> ProductService:
    return ProductService(ProductRepository(connection), ActivityRepository(connection))


def get_warehouse_service(
    connection: Annotated[Connection, Depends(get_db_connection)],
) -> WarehouseService:
    return WarehouseService(WarehouseRepository(connection), ActivityRepository(connection))


def get_inventory_service(
    connection: Annotated[Connection, Depends(get_db_connection)],
) -> InventoryService:
    return InventoryService(
        InventoryRepository(connection),
        AlertRepository(connection),
        ActivityRepository(connection),
    )


def get_supplier_service(
    connection: Annotated[Connection, Depends(get_db_connection)],
) -> SupplierService:
    return SupplierService(SupplierRepository(connection), ActivityRepository(connection))


def get_order_service(
    connection: Annotated[Connection, Depends(get_db_connection)],
) -> OrderService:
    return OrderService(
        OrderRepository(connection),
        InventoryRepository(connection),
        AlertRepository(connection),
        ActivityRepository(connection),
    )


def get_alert_service(
    connection: Annotated[Connection, Depends(get_db_connection)],
) -> AlertService:
    return AlertService(AlertRepository(connection), OrderRepository(connection), ActivityRepository(connection))


def get_activity_service(
    connection: Annotated[Connection, Depends(get_db_connection)],
) -> ActivityService:
    return ActivityService(ActivityRepository(connection))


def get_analytics_service(
    connection: Annotated[Connection, Depends(get_db_connection)],
) -> AnalyticsService:
    return AnalyticsService(AnalyticsRepository(connection))


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> CurrentUser:
    if not credentials:
        from app.core.exceptions import AuthenticationError

        raise AuthenticationError()
    payload = decode_access_token(credentials.credentials, settings)
    token_payload = TokenPayload(**payload)
    return CurrentUser(
        user_id=token_payload.sub,
        workspace_id=token_payload.workspace_id,
        role=token_payload.role,
    )
