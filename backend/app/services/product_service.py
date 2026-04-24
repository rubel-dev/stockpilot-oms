import re

from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.core.pagination import normalize_pagination
from app.repositories.activity_repository import ActivityRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductDetailResponse, ProductListResponse
from app.services.auth_service import CurrentUser


class ProductService:
    def __init__(
        self,
        product_repository: ProductRepository,
        activity_repository: ActivityRepository,
    ) -> None:
        self.product_repository = product_repository
        self.activity_repository = activity_repository

    def list_products(
        self,
        current_user: CurrentUser,
        *,
        page: int,
        page_size: int,
        search: str | None,
        category_id: str | None,
        status: str | None,
        sort: str,
        direction: str,
    ) -> ProductListResponse:
        pagination = normalize_pagination(page, page_size)
        safe_sort = sort if sort in self.product_repository.SORT_FIELDS else "updated_at"
        safe_direction = direction.lower() if direction.lower() in {"asc", "desc"} else "desc"
        items = self.product_repository.list_products(
            workspace_id=current_user.workspace_id,
            pagination_offset=pagination.offset,
            page_size=pagination.page_size,
            search=search.strip() if search else None,
            category_id=category_id,
            status=status,
            sort_field=safe_sort,
            sort_direction=safe_direction,
        )
        total = self.product_repository.count_products(
            workspace_id=current_user.workspace_id,
            search=search.strip() if search else None,
            category_id=category_id,
            status=status,
        )
        return ProductListResponse(
            items=items,
            page=pagination.page,
            page_size=pagination.page_size,
            total=total,
        )

    def get_product(self, current_user: CurrentUser, product_id: str) -> ProductDetailResponse:
        row = self.product_repository.get_product_detail(current_user.workspace_id, product_id)
        if not row:
            raise NotFoundError("Product not found.")
        return ProductDetailResponse(**row)

    def create_product(self, current_user: CurrentUser, payload: dict) -> ProductDetailResponse:
        category_id = payload.get("category_id")
        if category_id and not self.product_repository.category_exists(current_user.workspace_id, category_id):
            raise ValidationAppError("Selected category does not exist in this workspace.")

        sku = self._build_unique_sku(current_user.workspace_id, payload["name"], payload.get("sku"))
        with self.product_repository.connection.transaction():
            created = self.product_repository.create_product(
                {
                    "workspace_id": current_user.workspace_id,
                    "category_id": category_id,
                    "name": payload["name"].strip(),
                    "sku": sku,
                    "description": payload.get("description"),
                    "unit": payload.get("unit", "each").strip(),
                    "reorder_point": payload.get("reorder_point", 0),
                    "reorder_quantity": payload.get("reorder_quantity", 0),
                    "created_by": current_user.user_id,
                }
            )
            self.activity_repository.create_log(
                workspace_id=current_user.workspace_id,
                actor_user_id=current_user.user_id,
                action="product.created",
                entity_type="product",
                entity_id=created["id"],
                summary=f"Created product {payload['name'].strip()}",
                metadata={"sku": sku},
            )
        return self.get_product(current_user, created["id"])

    def update_product(self, current_user: CurrentUser, product_id: str, payload: dict) -> ProductDetailResponse:
        existing = self.product_repository.get_product_detail(current_user.workspace_id, product_id)
        if not existing:
            raise NotFoundError("Product not found.")

        category_id = payload.get("category_id")
        if category_id and not self.product_repository.category_exists(current_user.workspace_id, category_id):
            raise ValidationAppError("Selected category does not exist in this workspace.")

        fields: dict[str, object] = {}
        for key in ["name", "category_id", "description", "unit", "reorder_point", "reorder_quantity", "status"]:
            if key in payload and payload[key] is not None:
                fields[key] = payload[key].strip() if isinstance(payload[key], str) else payload[key]

        if payload.get("sku") is not None:
            sku = payload["sku"].strip()
            if self.product_repository.sku_exists(current_user.workspace_id, sku, exclude_product_id=product_id):
                raise ConflictError("A product with this SKU already exists in the workspace.")
            fields["sku"] = sku

        if not fields:
            return ProductDetailResponse(**existing)

        with self.product_repository.connection.transaction():
            self.product_repository.update_product(current_user.workspace_id, product_id, fields)
            self.activity_repository.create_log(
                workspace_id=current_user.workspace_id,
                actor_user_id=current_user.user_id,
                action="product.updated",
                entity_type="product",
                entity_id=product_id,
                summary=f"Updated product {existing['name']}",
            )
        return self.get_product(current_user, product_id)

    def archive_product(self, current_user: CurrentUser, product_id: str) -> ProductDetailResponse:
        existing = self.product_repository.get_product_detail(current_user.workspace_id, product_id)
        if not existing:
            raise NotFoundError("Product not found.")
        with self.product_repository.connection.transaction():
            self.product_repository.update_product(
                current_user.workspace_id,
                product_id,
                {"status": "archived"},
            )
            self.activity_repository.create_log(
                workspace_id=current_user.workspace_id,
                actor_user_id=current_user.user_id,
                action="product.archived",
                entity_type="product",
                entity_id=product_id,
                summary=f"Archived product {existing['name']}",
            )
        return self.get_product(current_user, product_id)

    def _build_unique_sku(self, workspace_id: str, name: str, submitted_sku: str | None) -> str:
        if submitted_sku:
            candidate = submitted_sku.strip().upper()
            if self.product_repository.sku_exists(workspace_id, candidate):
                raise ConflictError("A product with this SKU already exists in the workspace.")
            return candidate

        base = re.sub(r"[^A-Z0-9]+", "-", name.upper()).strip("-") or "SKU"
        candidate = base[:40]
        suffix = 1
        while self.product_repository.sku_exists(workspace_id, candidate):
            suffix += 1
            candidate = f"{base[:35]}-{suffix}"
        return candidate
