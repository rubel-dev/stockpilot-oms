from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.core.pagination import normalize_pagination
from app.repositories.activity_repository import ActivityRepository
from app.repositories.supplier_repository import SupplierRepository
from app.schemas.supplier import SupplierDetailResponse, SupplierListResponse
from app.services.auth_service import CurrentUser


class SupplierService:
    def __init__(self, supplier_repository: SupplierRepository, activity_repository: ActivityRepository) -> None:
        self.supplier_repository = supplier_repository
        self.activity_repository = activity_repository

    def list_suppliers(self, current_user: CurrentUser, *, page: int, page_size: int, search: str | None, status: str | None, sort: str, direction: str) -> SupplierListResponse:
        pagination = normalize_pagination(page, page_size)
        items = self.supplier_repository.list_suppliers(
            workspace_id=current_user.workspace_id,
            page_size=pagination.page_size,
            offset=pagination.offset,
            search=search.strip() if search else None,
            status=status,
            sort_field=sort,
            sort_direction=direction.lower(),
        )
        total = self.supplier_repository.count_suppliers(
            workspace_id=current_user.workspace_id,
            search=search.strip() if search else None,
            status=status,
        )
        return SupplierListResponse(items=items, page=pagination.page, page_size=pagination.page_size, total=total)

    def get_supplier(self, current_user: CurrentUser, supplier_id: str) -> SupplierDetailResponse:
        supplier = self.supplier_repository.get_supplier_detail(current_user.workspace_id, supplier_id)
        if not supplier:
            raise NotFoundError("Supplier not found.")
        links = self.supplier_repository.list_supplier_links(current_user.workspace_id, supplier_id)
        return SupplierDetailResponse(**supplier, linked_products=links)

    def create_supplier(self, current_user: CurrentUser, payload: dict) -> SupplierDetailResponse:
        with self.supplier_repository.connection.transaction():
            supplier = self.supplier_repository.create_supplier({"workspace_id": current_user.workspace_id, **payload})
            self.activity_repository.create_log(
                workspace_id=current_user.workspace_id,
                actor_user_id=current_user.user_id,
                action="supplier.created",
                entity_type="supplier",
                entity_id=supplier["id"],
                summary=f"Created supplier {payload['name'].strip()}",
            )
        return self.get_supplier(current_user, supplier["id"])

    def update_supplier(self, current_user: CurrentUser, supplier_id: str, payload: dict) -> SupplierDetailResponse:
        existing = self.supplier_repository.get_supplier_detail(current_user.workspace_id, supplier_id)
        if not existing:
            raise NotFoundError("Supplier not found.")
        if not payload:
            return self.get_supplier(current_user, supplier_id)
        normalized = {k: v.strip() if isinstance(v, str) else v for k, v in payload.items() if v is not None}
        with self.supplier_repository.connection.transaction():
            self.supplier_repository.update_supplier(current_user.workspace_id, supplier_id, normalized)
            self.activity_repository.create_log(
                workspace_id=current_user.workspace_id,
                actor_user_id=current_user.user_id,
                action="supplier.updated",
                entity_type="supplier",
                entity_id=supplier_id,
                summary=f"Updated supplier {existing['name']}",
            )
        return self.get_supplier(current_user, supplier_id)

    def link_product(self, current_user: CurrentUser, supplier_id: str, payload: dict) -> SupplierDetailResponse:
        supplier = self.supplier_repository.get_supplier_detail(current_user.workspace_id, supplier_id)
        if not supplier:
            raise NotFoundError("Supplier not found.")
        if not self.supplier_repository.product_exists(current_user.workspace_id, payload["product_id"]):
            raise NotFoundError("Product not found.")
        if self.supplier_repository.supplier_product_exists(current_user.workspace_id, supplier_id, payload["product_id"]):
            raise ConflictError("This supplier is already linked to the product.")
        with self.supplier_repository.connection.transaction():
            self.supplier_repository.link_product(
                workspace_id=current_user.workspace_id,
                supplier_id=supplier_id,
                payload=payload,
            )
            self.activity_repository.create_log(
                workspace_id=current_user.workspace_id,
                actor_user_id=current_user.user_id,
                action="supplier.product_linked",
                entity_type="supplier",
                entity_id=supplier_id,
                summary=f"Linked a product to supplier {supplier['name']}",
                metadata={"product_id": payload["product_id"]},
            )
        return self.get_supplier(current_user, supplier_id)

    def unlink_product(self, current_user: CurrentUser, supplier_id: str, product_id: str) -> None:
        supplier = self.supplier_repository.get_supplier_detail(current_user.workspace_id, supplier_id)
        if not supplier:
            raise NotFoundError("Supplier not found.")
        with self.supplier_repository.connection.transaction():
            deleted = self.supplier_repository.unlink_product(current_user.workspace_id, supplier_id, product_id)
            if not deleted:
                raise NotFoundError("Supplier-product link not found.")
            self.activity_repository.create_log(
                workspace_id=current_user.workspace_id,
                actor_user_id=current_user.user_id,
                action="supplier.product_unlinked",
                entity_type="supplier",
                entity_id=supplier_id,
                summary=f"Unlinked a product from supplier {supplier['name']}",
                metadata={"product_id": product_id},
            )

