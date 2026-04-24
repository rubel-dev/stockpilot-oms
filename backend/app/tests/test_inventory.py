from datetime import UTC, datetime

from app.core.exceptions import InsufficientStockError
from app.services.auth_service import CurrentUser
from app.services.inventory_service import InventoryService


class FakeTransaction:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeConnection:
    def transaction(self):
        return FakeTransaction()


class FakeInventoryRepository:
    def __init__(self) -> None:
        self.connection = FakeConnection()
        self.products = {
            "product-1": {
                "id": "product-1",
                "workspace_id": "ws-1",
                "name": "Edge Router",
                "sku": "EDGE-ROUTER",
                "reorder_point": 5,
                "status": "active",
            }
        }
        self.warehouses = {
            "wh-1": {"id": "wh-1", "workspace_id": "ws-1", "name": "Dhaka", "code": "DHK", "status": "active"},
            "wh-2": {"id": "wh-2", "workspace_id": "ws-1", "name": "Chattogram", "code": "CTG", "status": "active"},
        }
        self.balances = {
            ("product-1", "wh-1"): {
                "id": "bal-1",
                "workspace_id": "ws-1",
                "product_id": "product-1",
                "warehouse_id": "wh-1",
                "on_hand_quantity": 10,
                "reserved_quantity": 2,
                "updated_at": datetime.now(UTC),
            }
        }
        self.movements = []

    def get_product(self, workspace_id: str, product_id: str):
        return self.products.get(product_id)

    def get_warehouse(self, workspace_id: str, warehouse_id: str):
        return self.warehouses.get(warehouse_id)

    def get_balance_for_update(self, workspace_id: str, product_id: str, warehouse_id: str):
        return self.balances.get((product_id, warehouse_id))

    def create_balance(self, workspace_id: str, product_id: str, warehouse_id: str):
        row = {
            "id": f"bal-{len(self.balances)+1}",
            "workspace_id": workspace_id,
            "product_id": product_id,
            "warehouse_id": warehouse_id,
            "on_hand_quantity": 0,
            "reserved_quantity": 0,
            "updated_at": datetime.now(UTC),
        }
        self.balances[(product_id, warehouse_id)] = row
        return row

    def update_balance(self, *, balance_id: str, on_hand_quantity: int, reserved_quantity: int):
        for row in self.balances.values():
            if row["id"] == balance_id:
                row["on_hand_quantity"] = on_hand_quantity
                row["reserved_quantity"] = reserved_quantity
                row["updated_at"] = datetime.now(UTC)
                break

    def insert_movement(self, **kwargs):
        movement_id = f"move-{len(self.movements)+1}"
        self.movements.append({"id": movement_id, **kwargs, "created_at": datetime.now(UTC)})
        return {"id": movement_id}

    def list_movements(self, **kwargs):
        result = []
        for movement in reversed(self.movements):
            product = self.products[movement["product_id"]]
            warehouse = self.warehouses[movement["warehouse_id"]]
            destination = self.warehouses.get(movement["destination_warehouse_id"])
            result.append(
                {
                    "id": movement["id"],
                    "workspace_id": movement["workspace_id"],
                    "product_id": movement["product_id"],
                    "product_name": product["name"],
                    "product_sku": product["sku"],
                    "warehouse_id": movement["warehouse_id"],
                    "warehouse_name": warehouse["name"],
                    "destination_warehouse_id": movement["destination_warehouse_id"],
                    "destination_warehouse_name": destination["name"] if destination else None,
                    "movement_type": movement["movement_type"],
                    "quantity": movement["quantity"],
                    "quantity_before": movement["quantity_before"],
                    "quantity_after": movement["quantity_after"],
                    "reason": movement["reason"],
                    "reference_type": movement["reference_type"],
                    "reference_id": movement["reference_id"],
                    "notes": movement["notes"],
                    "created_by": movement["created_by"],
                    "created_by_name": "Rubel",
                    "created_at": movement["created_at"],
                }
            )
        return result[: kwargs["page_size"]]

    def count_movements(self, **kwargs):
        return len(self.movements)

    def list_balances(self, **kwargs):
        return []

    def count_balances(self, **kwargs):
        return 0


class FakeAlertRepository:
    def __init__(self) -> None:
        self.connection = FakeConnection()
        self.open_alerts = {}

    def find_open_alert(self, *, workspace_id: str, alert_type: str, product_id: str | None = None, warehouse_id: str | None = None, order_id: str | None = None):
        return self.open_alerts.get((alert_type, product_id, warehouse_id, order_id))

    def create_alert(self, **kwargs):
        self.open_alerts[(kwargs["alert_type"], kwargs["product_id"], kwargs["warehouse_id"], kwargs["order_id"])] = {"id": "alert-1"}
        return {"id": "alert-1"}

    def resolve_open_alert(self, *, workspace_id: str, alert_type: str, product_id: str | None = None, warehouse_id: str | None = None, order_id: str | None = None, resolved_by: str | None = None):
        self.open_alerts.pop((alert_type, product_id, warehouse_id, order_id), None)


class FakeActivityRepository:
    def __init__(self) -> None:
        self.logs = []

    def create_log(self, **kwargs):
        self.logs.append(kwargs)


def test_stock_out_prevents_negative_available_stock():
    inventory_repo = FakeInventoryRepository()
    service = InventoryService(inventory_repo, FakeAlertRepository(), FakeActivityRepository())
    current_user = CurrentUser(user_id="user-1", workspace_id="ws-1", role="owner")

    try:
        service.stock_out(
            current_user,
            {"product_id": "product-1", "warehouse_id": "wh-1", "quantity": 20, "reason": "damage"},
        )
        assert False, "Expected insufficient stock"
    except InsufficientStockError:
        assert True


def test_transfer_moves_stock_between_warehouses_and_creates_destination_balance():
    inventory_repo = FakeInventoryRepository()
    alerts = FakeAlertRepository()
    activity = FakeActivityRepository()
    service = InventoryService(inventory_repo, alerts, activity)
    current_user = CurrentUser(user_id="user-1", workspace_id="ws-1", role="owner")

    service.transfer(
        current_user,
        {
            "product_id": "product-1",
            "source_warehouse_id": "wh-1",
            "destination_warehouse_id": "wh-2",
            "quantity": 3,
            "reason": "rebalance",
        },
    )

    assert inventory_repo.balances[("product-1", "wh-1")]["on_hand_quantity"] == 7
    assert inventory_repo.balances[("product-1", "wh-2")]["on_hand_quantity"] == 3
    assert len(inventory_repo.movements) == 2


def test_low_stock_alert_generated_when_available_drops_to_reorder_point():
    inventory_repo = FakeInventoryRepository()
    alerts = FakeAlertRepository()
    service = InventoryService(inventory_repo, alerts, FakeActivityRepository())
    current_user = CurrentUser(user_id="user-1", workspace_id="ws-1", role="owner")

    service.stock_out(
        current_user,
        {"product_id": "product-1", "warehouse_id": "wh-1", "quantity": 3, "reason": "manual"},
    )

    assert ("low_stock", "product-1", "wh-1", None) in alerts.open_alerts

