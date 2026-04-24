from datetime import UTC, datetime

from app.core.exceptions import InsufficientStockError
from app.services.auth_service import CurrentUser
from app.services.order_service import OrderService


class FakeTransaction:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeConnection:
    def transaction(self):
        return FakeTransaction()


class FakeOrderRepository:
    def __init__(self) -> None:
        self.connection = FakeConnection()
        self.orders = {
            "order-1": {
                "id": "order-1",
                "workspace_id": "ws-1",
                "order_number": "SO-2026-0001",
                "order_type": "sales",
                "status": "draft",
                "warehouse_id": "wh-1",
                "warehouse_name": "Dhaka",
                "supplier_id": None,
                "supplier_name": None,
                "customer_name": "Acme",
                "notes": None,
                "subtotal_amount": 100.0,
                "created_by": "user-1",
                "confirmed_at": None,
                "processed_at": None,
                "shipped_at": None,
                "completed_at": None,
                "cancelled_at": None,
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            }
        }
        self.items = {
            "order-1": [
                {
                    "id": "item-1",
                    "product_id": "product-1",
                    "product_name": "Edge Router",
                    "product_sku": "EDGE-ROUTER",
                    "quantity": 4,
                    "unit_price": 25.0,
                    "unit_cost": None,
                    "line_total": 100.0,
                    "created_at": datetime.now(UTC),
                    "updated_at": datetime.now(UTC),
                }
            ]
        }

    def get_order_detail(self, workspace_id: str, order_id: str):
        return self.orders.get(order_id)

    def list_order_items(self, workspace_id: str, order_id: str):
        return self.items.get(order_id, [])

    def update_order_header(self, workspace_id: str, order_id: str, fields: dict[str, object]):
        self.orders[order_id].update(fields)

    def list_orders(self, **kwargs):
        return []

    def count_orders(self, **kwargs):
        return 0

    def warehouse_exists(self, workspace_id: str, warehouse_id: str) -> bool:
        return True

    def supplier_exists(self, workspace_id: str, supplier_id: str) -> bool:
        return True

    def supplier_product_exists(self, workspace_id: str, supplier_id: str, product_id: str) -> bool:
        return True

    def products_for_ids(self, workspace_id: str, product_ids: list[str]):
        return [{"id": product_ids[0], "name": "Edge Router", "sku": "EDGE-ROUTER"}]

    def next_order_number(self, workspace_id: str, order_type: str) -> str:
        return "SO-2026-9999"

    def create_order(self, payload: dict):
        return {"id": "order-2"}

    def insert_order_item(self, payload: dict):
        return None

    def replace_order_items(self, workspace_id: str, order_id: str, items: list[dict]):
        self.items[order_id] = items


class FakeInventoryRepository:
    def __init__(self) -> None:
        self.balances = {
            ("product-1", "wh-1"): {
                "id": "bal-1",
                "on_hand_quantity": 10,
                "reserved_quantity": 0,
            }
        }
        self.products = {"product-1": {"id": "product-1", "workspace_id": "ws-1", "name": "Edge Router", "sku": "EDGE-ROUTER", "reorder_point": 3}}
        self.warehouses = {"wh-1": {"id": "wh-1", "workspace_id": "ws-1", "name": "Dhaka"}}
        self.movements = []

    def get_balance_for_update(self, workspace_id: str, product_id: str, warehouse_id: str):
        return self.balances.get((product_id, warehouse_id))

    def update_balance(self, *, balance_id: str, on_hand_quantity: int, reserved_quantity: int):
        self.balances[("product-1", "wh-1")]["on_hand_quantity"] = on_hand_quantity
        self.balances[("product-1", "wh-1")]["reserved_quantity"] = reserved_quantity

    def insert_movement(self, **kwargs):
        self.movements.append(kwargs)
        return {"id": f"move-{len(self.movements)}"}

    def get_product(self, workspace_id: str, product_id: str):
        return self.products.get(product_id)

    def get_warehouse(self, workspace_id: str, warehouse_id: str):
        return self.warehouses.get(warehouse_id)

    def create_balance(self, workspace_id: str, product_id: str, warehouse_id: str):
        row = {"id": "bal-new", "on_hand_quantity": 0, "reserved_quantity": 0}
        self.balances[(product_id, warehouse_id)] = row
        return row


class FakeAlertRepository:
    def __init__(self) -> None:
        self.resolved = []
        self.created = []
        self.open = {}

    def find_open_alert(self, **kwargs):
        return self.open.get((kwargs["alert_type"], kwargs.get("product_id"), kwargs.get("warehouse_id"), kwargs.get("order_id")))

    def create_alert(self, **kwargs):
        self.created.append(kwargs)
        self.open[(kwargs["alert_type"], kwargs.get("product_id"), kwargs.get("warehouse_id"), kwargs.get("order_id"))] = {"id": "alert-1"}
        return {"id": "alert-1"}

    def resolve_open_alert(self, **kwargs):
        self.resolved.append(kwargs)
        self.open.pop((kwargs["alert_type"], kwargs.get("product_id"), kwargs.get("warehouse_id"), kwargs.get("order_id")), None)


class FakeActivityRepository:
    def __init__(self) -> None:
        self.logs = []

    def create_log(self, **kwargs):
        self.logs.append(kwargs)


def build_service():
    return OrderService(FakeOrderRepository(), FakeInventoryRepository(), FakeAlertRepository(), FakeActivityRepository())


def test_confirm_sales_order_reserves_stock():
    service = build_service()
    current_user = CurrentUser(user_id="user-1", workspace_id="ws-1", role="owner")

    order = service.confirm_order(current_user, "order-1")

    assert order.status == "confirmed"
    assert service.inventory_repository.balances[("product-1", "wh-1")]["reserved_quantity"] == 4


def test_confirm_sales_order_prevents_overselling():
    service = build_service()
    service.inventory_repository.balances[("product-1", "wh-1")]["on_hand_quantity"] = 2
    current_user = CurrentUser(user_id="user-1", workspace_id="ws-1", role="owner")

    try:
        service.confirm_order(current_user, "order-1")
        assert False, "Expected insufficient stock"
    except InsufficientStockError:
        assert True


def test_cancel_sales_order_releases_reserved_stock():
    service = build_service()
    current_user = CurrentUser(user_id="user-1", workspace_id="ws-1", role="owner")
    service.confirm_order(current_user, "order-1")
    service.order_repository.orders["order-1"]["status"] = "confirmed"

    order = service.cancel_order(current_user, "order-1")

    assert order.status == "cancelled"
    assert service.inventory_repository.balances[("product-1", "wh-1")]["reserved_quantity"] == 0

