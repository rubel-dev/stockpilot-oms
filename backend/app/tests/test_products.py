from datetime import datetime, UTC

from app.core.exceptions import ConflictError, NotFoundError
from app.services.auth_service import CurrentUser
from app.services.product_service import ProductService


class FakeProductRepository:
    SORT_FIELDS = {"updated_at": object(), "name": object(), "sku": object(), "created_at": object()}

    def __init__(self) -> None:
        self.connection = __import__("app.tests.conftest", fromlist=["FakeConnection"]).FakeConnection()
        self.products = {}
        self.categories = {"cat-1"}

    def category_exists(self, workspace_id: str, category_id: str) -> bool:
        return category_id in self.categories

    def sku_exists(self, workspace_id: str, sku: str, exclude_product_id: str | None = None) -> bool:
        return any(
            product["sku"] == sku and product["id"] != exclude_product_id
            for product in self.products.values()
        )

    def create_product(self, payload: dict):
        product_id = f"product-{len(self.products) + 1}"
        self.products[product_id] = {
            "id": product_id,
            "workspace_id": payload["workspace_id"],
            "category_id": payload["category_id"],
            "category_name": "Networking" if payload["category_id"] else None,
            "name": payload["name"],
            "sku": payload["sku"],
            "description": payload["description"],
            "unit": payload["unit"],
            "reorder_point": payload["reorder_point"],
            "reorder_quantity": payload["reorder_quantity"],
            "status": "active",
            "created_by": payload["created_by"],
            "total_on_hand": 0,
            "total_reserved": 0,
            "total_available": 0,
            "warehouse_count": 0,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }
        return {"id": product_id}

    def get_product_detail(self, workspace_id: str, product_id: str):
        return self.products.get(product_id)

    def list_products(self, **kwargs):
        return list(self.products.values())

    def count_products(self, **kwargs):
        return len(self.products)

    def update_product(self, workspace_id: str, product_id: str, fields: dict):
        self.products[product_id].update(fields)

class FakeActivityRepository:
    def create_log(self, **kwargs):
        return None


def test_create_product_generates_unique_sku():
    repo = FakeProductRepository()
    service = ProductService(repo, FakeActivityRepository())
    current_user = CurrentUser(user_id="user-1", workspace_id="ws-1", role="owner")

    product = service.create_product(
        current_user,
        {
            "name": "Edge Router",
            "category_id": "cat-1",
            "description": "Test",
            "unit": "each",
            "reorder_point": 10,
            "reorder_quantity": 20,
        },
    )

    assert product.sku == "EDGE-ROUTER"


def test_create_product_rejects_duplicate_sku():
    repo = FakeProductRepository()
    repo.products["product-1"] = {
        "id": "product-1",
        "workspace_id": "ws-1",
        "category_id": None,
        "category_name": None,
        "name": "Existing",
        "sku": "EXISTING-SKU",
        "description": None,
        "unit": "each",
        "reorder_point": 0,
        "reorder_quantity": 0,
        "status": "active",
        "created_by": "user-1",
        "total_on_hand": 0,
        "total_reserved": 0,
        "total_available": 0,
        "warehouse_count": 0,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    service = ProductService(repo, FakeActivityRepository())
    current_user = CurrentUser(user_id="user-1", workspace_id="ws-1", role="owner")

    try:
        service.create_product(
            current_user,
            {
                "name": "Another Product",
                "sku": "EXISTING-SKU",
                "category_id": None,
                "description": None,
                "unit": "each",
                "reorder_point": 0,
                "reorder_quantity": 0,
            },
        )
        assert False, "Expected duplicate SKU conflict"
    except ConflictError:
        assert True


def test_archive_missing_product_raises_not_found():
    service = ProductService(FakeProductRepository(), FakeActivityRepository())
    current_user = CurrentUser(user_id="user-1", workspace_id="ws-1", role="owner")

    try:
        service.archive_product(current_user, "missing-product")
        assert False, "Expected not found"
    except NotFoundError:
        assert True
