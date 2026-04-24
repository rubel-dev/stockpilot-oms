from datetime import datetime, UTC

from app.core.exceptions import ConflictError, NotFoundError
from app.services.auth_service import CurrentUser
from app.services.warehouse_service import WarehouseService


class FakeWarehouseRepository:
    SORT_FIELDS = {"updated_at": object(), "name": object(), "code": object(), "created_at": object()}

    def __init__(self) -> None:
        self.connection = __import__("app.tests.conftest", fromlist=["FakeConnection"]).FakeConnection()
        self.warehouses = {}

    def code_exists(self, workspace_id: str, code: str, exclude_warehouse_id: str | None = None) -> bool:
        return any(
            warehouse["code"] == code and warehouse["id"] != exclude_warehouse_id
            for warehouse in self.warehouses.values()
        )

    def create_warehouse(self, payload: dict):
        warehouse_id = f"warehouse-{len(self.warehouses) + 1}"
        self.warehouses[warehouse_id] = {
            "id": warehouse_id,
            "workspace_id": payload["workspace_id"],
            "name": payload["name"],
            "code": payload["code"],
            "address_line1": payload["address_line1"],
            "address_line2": payload["address_line2"],
            "city": payload["city"],
            "state_region": payload["state_region"],
            "postal_code": payload["postal_code"],
            "country": payload["country"],
            "status": "active",
            "total_skus": 0,
            "total_units": 0,
            "total_reserved": 0,
            "low_stock_items": 0,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }
        return {"id": warehouse_id}

    def get_warehouse_detail(self, workspace_id: str, warehouse_id: str):
        return self.warehouses.get(warehouse_id)

    def list_warehouses(self, **kwargs):
        return list(self.warehouses.values())

    def count_warehouses(self, **kwargs):
        return len(self.warehouses)

    def update_warehouse(self, workspace_id: str, warehouse_id: str, fields: dict):
        self.warehouses[warehouse_id].update(fields)

class FakeActivityRepository:
    def create_log(self, **kwargs):
        return None


def test_create_warehouse_normalizes_uppercase_code():
    service = WarehouseService(FakeWarehouseRepository(), FakeActivityRepository())
    current_user = CurrentUser(user_id="user-1", workspace_id="ws-1", role="owner")

    warehouse = service.create_warehouse(
        current_user,
        {
            "name": "Dhaka Central",
            "code": "dhk-cen",
            "address_line1": None,
            "address_line2": None,
            "city": "Dhaka",
            "state_region": None,
            "postal_code": None,
            "country": "Bangladesh",
        },
    )

    assert warehouse.code == "DHK-CEN"


def test_duplicate_warehouse_code_raises_conflict():
    repo = FakeWarehouseRepository()
    repo.warehouses["warehouse-1"] = {
        "id": "warehouse-1",
        "workspace_id": "ws-1",
        "name": "Existing",
        "code": "DHK-CEN",
        "address_line1": None,
        "address_line2": None,
        "city": None,
        "state_region": None,
        "postal_code": None,
        "country": None,
        "status": "active",
        "total_skus": 0,
        "total_units": 0,
        "total_reserved": 0,
        "low_stock_items": 0,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    service = WarehouseService(repo, FakeActivityRepository())
    current_user = CurrentUser(user_id="user-1", workspace_id="ws-1", role="owner")

    try:
        service.create_warehouse(
            current_user,
            {
                "name": "New",
                "code": "DHK-CEN",
                "address_line1": None,
                "address_line2": None,
                "city": None,
                "state_region": None,
                "postal_code": None,
                "country": None,
            },
        )
        assert False, "Expected duplicate code conflict"
    except ConflictError:
        assert True


def test_get_missing_warehouse_raises_not_found():
    service = WarehouseService(FakeWarehouseRepository(), FakeActivityRepository())
    current_user = CurrentUser(user_id="user-1", workspace_id="ws-1", role="owner")

    try:
        service.get_warehouse(current_user, "missing")
        assert False, "Expected missing warehouse"
    except NotFoundError:
        assert True
