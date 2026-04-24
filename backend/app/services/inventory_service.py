from app.core.exceptions import (
    InsufficientStockError,
    NotFoundError,
    ValidationAppError,
)
from app.core.pagination import normalize_pagination
from app.repositories.activity_repository import ActivityRepository
from app.repositories.alert_repository import AlertRepository
from app.repositories.inventory_repository import InventoryRepository
from app.schemas.inventory import (
    InventoryBalanceListResponse,
    InventoryMovementListResponse,
    InventoryMovementResponse,
)
from app.services.auth_service import CurrentUser


class InventoryService:
    def __init__(
        self,
        inventory_repository: InventoryRepository,
        alert_repository: AlertRepository,
        activity_repository: ActivityRepository,
    ) -> None:
        self.inventory_repository = inventory_repository
        self.alert_repository = alert_repository
        self.activity_repository = activity_repository

    def list_balances(
        self,
        current_user: CurrentUser,
        *,
        page: int,
        page_size: int,
        product_id: str | None,
        warehouse_id: str | None,
        low_stock: bool | None,
        search: str | None,
    ) -> InventoryBalanceListResponse:
        pagination = normalize_pagination(page, page_size)
        items = self.inventory_repository.list_balances(
            workspace_id=current_user.workspace_id,
            page_size=pagination.page_size,
            offset=pagination.offset,
            product_id=product_id,
            warehouse_id=warehouse_id,
            low_stock=low_stock,
            search=search.strip() if search else None,
        )
        total = self.inventory_repository.count_balances(
            workspace_id=current_user.workspace_id,
            product_id=product_id,
            warehouse_id=warehouse_id,
            low_stock=low_stock,
            search=search.strip() if search else None,
        )
        return InventoryBalanceListResponse(
            items=items,
            page=pagination.page,
            page_size=pagination.page_size,
            total=total,
        )

    def list_movements(
        self,
        current_user: CurrentUser,
        *,
        page: int,
        page_size: int,
        product_id: str | None,
        warehouse_id: str | None,
        movement_type: str | None,
        search: str | None,
    ) -> InventoryMovementListResponse:
        pagination = normalize_pagination(page, page_size)
        items = self.inventory_repository.list_movements(
            workspace_id=current_user.workspace_id,
            page_size=pagination.page_size,
            offset=pagination.offset,
            product_id=product_id,
            warehouse_id=warehouse_id,
            movement_type=movement_type,
            search=search.strip() if search else None,
        )
        total = self.inventory_repository.count_movements(
            workspace_id=current_user.workspace_id,
            product_id=product_id,
            warehouse_id=warehouse_id,
            movement_type=movement_type,
            search=search.strip() if search else None,
        )
        return InventoryMovementListResponse(
            items=items,
            page=pagination.page,
            page_size=pagination.page_size,
            total=total,
        )

    def stock_in(self, current_user: CurrentUser, payload: dict) -> InventoryMovementResponse:
        with self.inventory_repository.connection.transaction():
            product, warehouse = self._validate_product_and_warehouse(
                current_user.workspace_id,
                payload["product_id"],
                payload["warehouse_id"],
            )
            balance = self._get_or_create_balance(current_user.workspace_id, payload["product_id"], payload["warehouse_id"])
            before = balance["on_hand_quantity"]
            after = before + payload["quantity"]
            self.inventory_repository.update_balance(
                balance_id=balance["id"],
                on_hand_quantity=after,
                reserved_quantity=balance["reserved_quantity"],
            )
            movement = self.inventory_repository.insert_movement(
                workspace_id=current_user.workspace_id,
                product_id=payload["product_id"],
                warehouse_id=payload["warehouse_id"],
                destination_warehouse_id=None,
                movement_type="stock_in",
                quantity=payload["quantity"],
                quantity_before=before,
                quantity_after=after,
                reason=payload["reason"],
                reference_type=payload.get("reference_type"),
                reference_id=payload.get("reference_id"),
                notes=payload.get("notes"),
                created_by=current_user.user_id,
            )
            self.activity_repository.create_log(
                workspace_id=current_user.workspace_id,
                actor_user_id=current_user.user_id,
                action="inventory.stock_in",
                entity_type="inventory_movement",
                entity_id=movement["id"],
                summary=f"Added {payload['quantity']} units of {product['name']} to {warehouse['name']}",
                metadata={"product_id": product["id"], "warehouse_id": warehouse["id"], "quantity": payload["quantity"]},
            )
            self._sync_low_stock_alert(product, warehouse, after, balance["reserved_quantity"], current_user.user_id)
        return self.list_movements(current_user, page=1, page_size=1, product_id=payload["product_id"], warehouse_id=payload["warehouse_id"], movement_type=None, search=None).items[0]

    def stock_out(self, current_user: CurrentUser, payload: dict) -> InventoryMovementResponse:
        with self.inventory_repository.connection.transaction():
            product, warehouse = self._validate_product_and_warehouse(
                current_user.workspace_id,
                payload["product_id"],
                payload["warehouse_id"],
            )
            balance = self._get_or_create_balance(current_user.workspace_id, payload["product_id"], payload["warehouse_id"])
            available = balance["on_hand_quantity"] - balance["reserved_quantity"]
            if payload["quantity"] > available:
                raise InsufficientStockError()
            before = balance["on_hand_quantity"]
            after = before - payload["quantity"]
            self.inventory_repository.update_balance(
                balance_id=balance["id"],
                on_hand_quantity=after,
                reserved_quantity=balance["reserved_quantity"],
            )
            movement = self.inventory_repository.insert_movement(
                workspace_id=current_user.workspace_id,
                product_id=payload["product_id"],
                warehouse_id=payload["warehouse_id"],
                destination_warehouse_id=None,
                movement_type="stock_out",
                quantity=payload["quantity"],
                quantity_before=before,
                quantity_after=after,
                reason=payload["reason"],
                reference_type=payload.get("reference_type"),
                reference_id=payload.get("reference_id"),
                notes=payload.get("notes"),
                created_by=current_user.user_id,
            )
            self.activity_repository.create_log(
                workspace_id=current_user.workspace_id,
                actor_user_id=current_user.user_id,
                action="inventory.stock_out",
                entity_type="inventory_movement",
                entity_id=movement["id"],
                summary=f"Removed {payload['quantity']} units of {product['name']} from {warehouse['name']}",
                metadata={"product_id": product["id"], "warehouse_id": warehouse["id"], "quantity": payload["quantity"]},
            )
            self._sync_low_stock_alert(product, warehouse, after, balance["reserved_quantity"], current_user.user_id)
        return self.list_movements(current_user, page=1, page_size=1, product_id=payload["product_id"], warehouse_id=payload["warehouse_id"], movement_type=None, search=None).items[0]

    def transfer(self, current_user: CurrentUser, payload: dict) -> list[InventoryMovementResponse]:
        if payload["source_warehouse_id"] == payload["destination_warehouse_id"]:
            raise ValidationAppError("Source and destination warehouses must be different.")
        with self.inventory_repository.connection.transaction():
            product = self.inventory_repository.get_product(current_user.workspace_id, payload["product_id"])
            if not product:
                raise NotFoundError("Product not found.")
            source = self.inventory_repository.get_warehouse(current_user.workspace_id, payload["source_warehouse_id"])
            destination = self.inventory_repository.get_warehouse(current_user.workspace_id, payload["destination_warehouse_id"])
            if not source or not destination:
                raise NotFoundError("Warehouse not found.")
            if source["status"] != "active" or destination["status"] != "active":
                raise ValidationAppError("Only active warehouses can be used for transfers.")

            first_id, second_id = sorted([payload["source_warehouse_id"], payload["destination_warehouse_id"]])
            first_balance = self._get_or_create_balance(current_user.workspace_id, payload["product_id"], first_id)
            second_balance = self._get_or_create_balance(current_user.workspace_id, payload["product_id"], second_id)
            source_balance = first_balance if payload["source_warehouse_id"] == first_id else second_balance
            destination_balance = second_balance if payload["destination_warehouse_id"] == second_id else first_balance

            available = source_balance["on_hand_quantity"] - source_balance["reserved_quantity"]
            if payload["quantity"] > available:
                raise InsufficientStockError()

            source_before = source_balance["on_hand_quantity"]
            source_after = source_before - payload["quantity"]
            destination_before = destination_balance["on_hand_quantity"]
            destination_after = destination_before + payload["quantity"]

            self.inventory_repository.update_balance(
                balance_id=source_balance["id"],
                on_hand_quantity=source_after,
                reserved_quantity=source_balance["reserved_quantity"],
            )
            self.inventory_repository.update_balance(
                balance_id=destination_balance["id"],
                on_hand_quantity=destination_after,
                reserved_quantity=destination_balance["reserved_quantity"],
            )
            move_out = self.inventory_repository.insert_movement(
                workspace_id=current_user.workspace_id,
                product_id=payload["product_id"],
                warehouse_id=source["id"],
                destination_warehouse_id=destination["id"],
                movement_type="transfer_out",
                quantity=payload["quantity"],
                quantity_before=source_before,
                quantity_after=source_after,
                reason=payload["reason"],
                reference_type="manual",
                reference_id=None,
                notes=payload.get("notes"),
                created_by=current_user.user_id,
            )
            move_in = self.inventory_repository.insert_movement(
                workspace_id=current_user.workspace_id,
                product_id=payload["product_id"],
                warehouse_id=destination["id"],
                destination_warehouse_id=source["id"],
                movement_type="transfer_in",
                quantity=payload["quantity"],
                quantity_before=destination_before,
                quantity_after=destination_after,
                reason=payload["reason"],
                reference_type="manual",
                reference_id=None,
                notes=payload.get("notes"),
                created_by=current_user.user_id,
            )
            self.activity_repository.create_log(
                workspace_id=current_user.workspace_id,
                actor_user_id=current_user.user_id,
                action="inventory.transfer",
                entity_type="product",
                entity_id=product["id"],
                summary=f"Transferred {payload['quantity']} units of {product['name']} from {source['name']} to {destination['name']}",
                metadata={
                    "product_id": product["id"],
                    "source_warehouse_id": source["id"],
                    "destination_warehouse_id": destination["id"],
                    "quantity": payload["quantity"],
                },
            )
            self._sync_low_stock_alert(product, source, source_after, source_balance["reserved_quantity"], current_user.user_id)
            self._sync_low_stock_alert(product, destination, destination_after, destination_balance["reserved_quantity"], current_user.user_id)

        movement_rows = self.inventory_repository.list_movements(
            workspace_id=current_user.workspace_id,
            page_size=2,
            offset=0,
            product_id=payload["product_id"],
            warehouse_id=None,
            movement_type=None,
            search=None,
        )
        by_ids = {row["id"]: row for row in movement_rows}
        return [InventoryMovementResponse(**by_ids[move_out["id"]]), InventoryMovementResponse(**by_ids[move_in["id"]])]

    def adjust_stock(self, current_user: CurrentUser, payload: dict) -> InventoryMovementResponse:
        with self.inventory_repository.connection.transaction():
            product, warehouse = self._validate_product_and_warehouse(
                current_user.workspace_id,
                payload["product_id"],
                payload["warehouse_id"],
            )
            balance = self._get_or_create_balance(current_user.workspace_id, payload["product_id"], payload["warehouse_id"])
            if payload["counted_quantity"] < balance["reserved_quantity"]:
                raise ValidationAppError("Counted quantity cannot be below reserved stock.")
            before = balance["on_hand_quantity"]
            after = payload["counted_quantity"]
            quantity_delta = abs(after - before)
            self.inventory_repository.update_balance(
                balance_id=balance["id"],
                on_hand_quantity=after,
                reserved_quantity=balance["reserved_quantity"],
            )
            movement = self.inventory_repository.insert_movement(
                workspace_id=current_user.workspace_id,
                product_id=payload["product_id"],
                warehouse_id=payload["warehouse_id"],
                destination_warehouse_id=None,
                movement_type="adjustment",
                quantity=max(quantity_delta, 1),
                quantity_before=before,
                quantity_after=after,
                reason=payload["reason"],
                reference_type="manual",
                reference_id=None,
                notes=payload.get("notes"),
                created_by=current_user.user_id,
            )
            self.activity_repository.create_log(
                workspace_id=current_user.workspace_id,
                actor_user_id=current_user.user_id,
                action="inventory.adjustment",
                entity_type="inventory_movement",
                entity_id=movement["id"],
                summary=f"Adjusted {product['name']} in {warehouse['name']} from {before} to {after}",
                metadata={"before": before, "after": after},
            )
            self._sync_low_stock_alert(product, warehouse, after, balance["reserved_quantity"], current_user.user_id)
        return self.list_movements(current_user, page=1, page_size=1, product_id=payload["product_id"], warehouse_id=payload["warehouse_id"], movement_type=None, search=None).items[0]

    def _validate_product_and_warehouse(self, workspace_id: str, product_id: str, warehouse_id: str) -> tuple[dict, dict]:
        product = self.inventory_repository.get_product(workspace_id, product_id)
        warehouse = self.inventory_repository.get_warehouse(workspace_id, warehouse_id)
        if not product:
            raise NotFoundError("Product not found.")
        if not warehouse:
            raise NotFoundError("Warehouse not found.")
        if product["status"] != "active":
            raise ValidationAppError("Only active products can be moved.")
        if warehouse["status"] != "active":
            raise ValidationAppError("Only active warehouses can be used for inventory operations.")
        return product, warehouse

    def _get_or_create_balance(self, workspace_id: str, product_id: str, warehouse_id: str) -> dict:
        balance = self.inventory_repository.get_balance_for_update(workspace_id, product_id, warehouse_id)
        if balance:
            return balance
        return self.inventory_repository.create_balance(workspace_id, product_id, warehouse_id)

    def _sync_low_stock_alert(
        self,
        product: dict,
        warehouse: dict,
        on_hand_quantity: int,
        reserved_quantity: int,
        actor_user_id: str | None,
    ) -> None:
        available = on_hand_quantity - reserved_quantity
        if available <= product["reorder_point"]:
            existing = self.alert_repository.find_open_alert(
                workspace_id=product["workspace_id"],
                alert_type="low_stock",
                product_id=product["id"],
                warehouse_id=warehouse["id"],
            )
            if not existing:
                self.alert_repository.create_alert(
                    workspace_id=product["workspace_id"],
                    alert_type="low_stock",
                    severity="critical" if available == 0 else "warning",
                    product_id=product["id"],
                    warehouse_id=warehouse["id"],
                    order_id=None,
                    title=f"{product['name']} is low in {warehouse['name']}",
                    message=f"Available stock for {product['name']} is at or below reorder point in {warehouse['name']}.",
                    metadata={"available_quantity": available, "reorder_point": product["reorder_point"]},
                )
        else:
            self.alert_repository.resolve_open_alert(
                workspace_id=product["workspace_id"],
                alert_type="low_stock",
                product_id=product["id"],
                warehouse_id=warehouse["id"],
                resolved_by=actor_user_id,
            )

