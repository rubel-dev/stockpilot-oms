from collections import Counter

from app.core.exceptions import (
    InsufficientStockError,
    InvalidOrderTransitionError,
    NotFoundError,
    ValidationAppError,
)
from app.core.pagination import normalize_pagination
from app.repositories.activity_repository import ActivityRepository
from app.repositories.alert_repository import AlertRepository
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.order_repository import OrderRepository
from app.schemas.order import OrderDetailResponse, OrderListResponse
from app.services.auth_service import CurrentUser


class OrderService:
    def __init__(
        self,
        order_repository: OrderRepository,
        inventory_repository: InventoryRepository,
        alert_repository: AlertRepository,
        activity_repository: ActivityRepository,
    ) -> None:
        self.order_repository = order_repository
        self.inventory_repository = inventory_repository
        self.alert_repository = alert_repository
        self.activity_repository = activity_repository

    def list_orders(self, current_user: CurrentUser, *, page: int, page_size: int, order_type: str | None, status: str | None, supplier_id: str | None, warehouse_id: str | None, search: str | None, sort: str, direction: str) -> OrderListResponse:
        pagination = normalize_pagination(page, page_size)
        items = self.order_repository.list_orders(
            workspace_id=current_user.workspace_id,
            page_size=pagination.page_size,
            offset=pagination.offset,
            order_type=order_type,
            status=status,
            supplier_id=supplier_id,
            warehouse_id=warehouse_id,
            search=search.strip() if search else None,
            sort_field=sort,
            sort_direction=direction.lower(),
        )
        total = self.order_repository.count_orders(
            workspace_id=current_user.workspace_id,
            order_type=order_type,
            status=status,
            supplier_id=supplier_id,
            warehouse_id=warehouse_id,
            search=search.strip() if search else None,
        )
        return OrderListResponse(items=items, page=pagination.page, page_size=pagination.page_size, total=total)

    def get_order(self, current_user: CurrentUser, order_id: str) -> OrderDetailResponse:
        order = self.order_repository.get_order_detail(current_user.workspace_id, order_id)
        if not order:
            raise NotFoundError("Order not found.")
        items = self.order_repository.list_order_items(current_user.workspace_id, order_id)
        return OrderDetailResponse(**order, items=items)

    def create_order(self, current_user: CurrentUser, payload: dict) -> OrderDetailResponse:
        self._validate_order_payload(current_user.workspace_id, payload)
        subtotal = self._calculate_subtotal(payload)
        with self.order_repository.connection.transaction():
            order_number = self.order_repository.next_order_number(current_user.workspace_id, payload["order_type"])
            created = self.order_repository.create_order(
                {
                    "workspace_id": current_user.workspace_id,
                    "order_number": order_number,
                    "order_type": payload["order_type"],
                    "warehouse_id": payload["warehouse_id"],
                    "supplier_id": payload.get("supplier_id"),
                    "customer_name": payload.get("customer_name"),
                    "notes": payload.get("notes"),
                    "subtotal_amount": subtotal,
                    "created_by": current_user.user_id,
                }
            )
            for item in payload["items"]:
                self.order_repository.insert_order_item(
                    {
                        "workspace_id": current_user.workspace_id,
                        "order_id": created["id"],
                        "product_id": item["product_id"],
                        "quantity": item["quantity"],
                        "unit_price": item.get("unit_price"),
                        "unit_cost": item.get("unit_cost"),
                        "line_total": self._line_total(payload["order_type"], item),
                    }
                )
            self.activity_repository.create_log(
                workspace_id=current_user.workspace_id,
                actor_user_id=current_user.user_id,
                action="order.created",
                entity_type="order",
                entity_id=created["id"],
                summary=f"Created {payload['order_type']} order {order_number}",
            )
        return self.get_order(current_user, created["id"])

    def update_order(self, current_user: CurrentUser, order_id: str, payload: dict) -> OrderDetailResponse:
        order = self.get_order(current_user, order_id)
        if order.status != "draft":
            raise InvalidOrderTransitionError("Only draft orders can be updated.")
        updates = {}
        for key in ["supplier_id", "customer_name", "notes"]:
            if key in payload:
                updates[key] = payload[key]
        with self.order_repository.connection.transaction():
            if payload.get("items") is not None:
                candidate_payload = {
                    "order_type": order.order_type,
                    "warehouse_id": order.warehouse_id,
                    "supplier_id": payload.get("supplier_id", order.supplier_id),
                    "customer_name": payload.get("customer_name", order.customer_name),
                    "items": payload["items"],
                }
                self._validate_order_payload(current_user.workspace_id, candidate_payload)
                updates["subtotal_amount"] = self._calculate_subtotal({**candidate_payload, "items": payload["items"]})
                self.order_repository.replace_order_items(
                    current_user.workspace_id,
                    order_id,
                    [
                        {
                            "product_id": item["product_id"],
                            "quantity": item["quantity"],
                            "unit_price": item.get("unit_price"),
                            "unit_cost": item.get("unit_cost"),
                            "line_total": self._line_total(order.order_type, item),
                        }
                        for item in payload["items"]
                    ],
                )
            if updates:
                self.order_repository.update_order_header(current_user.workspace_id, order_id, updates)
            self.activity_repository.create_log(
                workspace_id=current_user.workspace_id,
                actor_user_id=current_user.user_id,
                action="order.updated",
                entity_type="order",
                entity_id=order_id,
                summary=f"Updated order {order.order_number}",
            )
        return self.get_order(current_user, order_id)

    def confirm_order(self, current_user: CurrentUser, order_id: str) -> OrderDetailResponse:
        order = self.get_order(current_user, order_id)
        if order.status != "draft":
            raise InvalidOrderTransitionError("Only draft orders can be confirmed.")
        with self.order_repository.connection.transaction():
            if order.order_type == "sales":
                self._reserve_sales_order_stock(current_user, order)
            else:
                for item in order.items:
                    if not self.order_repository.supplier_product_exists(current_user.workspace_id, order.supplier_id, item.product_id):
                        raise ValidationAppError("All purchase order items must be linked to the selected supplier.")
            self.order_repository.update_order_header(
                current_user.workspace_id,
                order_id,
                {"status": "confirmed", "confirmed_at": self._sql_now_marker()},
            )
            self.activity_repository.create_log(
                workspace_id=current_user.workspace_id,
                actor_user_id=current_user.user_id,
                action="order.confirmed",
                entity_type="order",
                entity_id=order_id,
                summary=f"Confirmed order {order.order_number}",
            )
            self._resolve_stale_order_alert(current_user.workspace_id, order_id, current_user.user_id)
        return self.get_order(current_user, order_id)

    def process_order(self, current_user: CurrentUser, order_id: str) -> OrderDetailResponse:
        order = self.get_order(current_user, order_id)
        if order.status != "confirmed":
            raise InvalidOrderTransitionError("Only confirmed orders can move to processing.")
        with self.order_repository.connection.transaction():
            self.order_repository.update_order_header(
                current_user.workspace_id,
                order_id,
                {"status": "processing", "processed_at": self._sql_now_marker()},
            )
            self.activity_repository.create_log(
                workspace_id=current_user.workspace_id,
                actor_user_id=current_user.user_id,
                action="order.processing",
                entity_type="order",
                entity_id=order_id,
                summary=f"Moved order {order.order_number} to processing",
            )
        return self.get_order(current_user, order_id)

    def ship_order(self, current_user: CurrentUser, order_id: str) -> OrderDetailResponse:
        order = self.get_order(current_user, order_id)
        if order.order_type != "sales" or order.status != "processing":
            raise InvalidOrderTransitionError("Only processing sales orders can be shipped.")
        with self.order_repository.connection.transaction():
            for item in order.items:
                balance = self.inventory_repository.get_balance_for_update(current_user.workspace_id, item.product_id, order.warehouse_id)
                if not balance or balance["reserved_quantity"] < item.quantity:
                    raise InsufficientStockError("Reserved stock is not sufficient to ship this order.")
                before = balance["on_hand_quantity"]
                after = before - item.quantity
                new_reserved = balance["reserved_quantity"] - item.quantity
                self.inventory_repository.update_balance(
                    balance_id=balance["id"],
                    on_hand_quantity=after,
                    reserved_quantity=new_reserved,
                )
                self.inventory_repository.insert_movement(
                    workspace_id=current_user.workspace_id,
                    product_id=item.product_id,
                    warehouse_id=order.warehouse_id,
                    destination_warehouse_id=None,
                    movement_type="order_deduction",
                    quantity=item.quantity,
                    quantity_before=before,
                    quantity_after=after,
                    reason="sales_order_shipment",
                    reference_type="order",
                    reference_id=order.id,
                    notes=f"Shipment for {order.order_number}",
                    created_by=current_user.user_id,
                )
                product = self.inventory_repository.get_product(current_user.workspace_id, item.product_id)
                warehouse = self.inventory_repository.get_warehouse(current_user.workspace_id, order.warehouse_id)
                self._sync_low_stock_alert(product, warehouse, after, new_reserved, current_user.user_id)
            self.order_repository.update_order_header(
                current_user.workspace_id,
                order_id,
                {"status": "shipped", "shipped_at": self._sql_now_marker()},
            )
            self.activity_repository.create_log(
                workspace_id=current_user.workspace_id,
                actor_user_id=current_user.user_id,
                action="order.shipped",
                entity_type="order",
                entity_id=order.id,
                summary=f"Shipped sales order {order.order_number}",
            )
        return self.get_order(current_user, order_id)

    def complete_order(self, current_user: CurrentUser, order_id: str) -> OrderDetailResponse:
        order = self.get_order(current_user, order_id)
        with self.order_repository.connection.transaction():
            if order.order_type == "sales":
                if order.status != "shipped":
                    raise InvalidOrderTransitionError("Sales orders must be shipped before completion.")
                self.order_repository.update_order_header(
                    current_user.workspace_id,
                    order_id,
                    {"status": "completed", "completed_at": self._sql_now_marker()},
                )
            else:
                if order.status not in {"confirmed", "processing"}:
                    raise InvalidOrderTransitionError("Purchase orders can only be completed from confirmed or processing.")
                for item in order.items:
                    balance = self.inventory_repository.get_balance_for_update(current_user.workspace_id, item.product_id, order.warehouse_id)
                    if not balance:
                        balance = self.inventory_repository.create_balance(current_user.workspace_id, item.product_id, order.warehouse_id)
                    before = balance["on_hand_quantity"]
                    after = before + item.quantity
                    self.inventory_repository.update_balance(
                        balance_id=balance["id"],
                        on_hand_quantity=after,
                        reserved_quantity=balance["reserved_quantity"],
                    )
                    self.inventory_repository.insert_movement(
                        workspace_id=current_user.workspace_id,
                        product_id=item.product_id,
                        warehouse_id=order.warehouse_id,
                        destination_warehouse_id=None,
                        movement_type="stock_in",
                        quantity=item.quantity,
                        quantity_before=before,
                        quantity_after=after,
                        reason="purchase_order_receipt",
                        reference_type="order",
                        reference_id=order.id,
                        notes=f"Purchase receipt for {order.order_number}",
                        created_by=current_user.user_id,
                    )
                    product = self.inventory_repository.get_product(current_user.workspace_id, item.product_id)
                    warehouse = self.inventory_repository.get_warehouse(current_user.workspace_id, order.warehouse_id)
                    self._sync_low_stock_alert(product, warehouse, after, balance["reserved_quantity"], current_user.user_id)
                self.order_repository.update_order_header(
                    current_user.workspace_id,
                    order_id,
                    {"status": "completed", "completed_at": self._sql_now_marker()},
                )
            self.activity_repository.create_log(
                workspace_id=current_user.workspace_id,
                actor_user_id=current_user.user_id,
                action="order.completed",
                entity_type="order",
                entity_id=order.id,
                summary=f"Completed order {order.order_number}",
            )
            self._resolve_stale_order_alert(current_user.workspace_id, order_id, current_user.user_id)
        return self.get_order(current_user, order_id)

    def cancel_order(self, current_user: CurrentUser, order_id: str) -> OrderDetailResponse:
        order = self.get_order(current_user, order_id)
        if order.status not in {"draft", "confirmed", "processing"}:
            raise InvalidOrderTransitionError("Only draft, confirmed, or processing orders can be cancelled.")
        with self.order_repository.connection.transaction():
            if order.order_type == "sales" and order.status in {"confirmed", "processing"}:
                for item in order.items:
                    balance = self.inventory_repository.get_balance_for_update(current_user.workspace_id, item.product_id, order.warehouse_id)
                    if not balance or balance["reserved_quantity"] < item.quantity:
                        raise InsufficientStockError("Reserved stock is not sufficient to release for cancellation.")
                    before_reserved = balance["reserved_quantity"]
                    new_reserved = before_reserved - item.quantity
                    self.inventory_repository.update_balance(
                        balance_id=balance["id"],
                        on_hand_quantity=balance["on_hand_quantity"],
                        reserved_quantity=new_reserved,
                    )
                    self.inventory_repository.insert_movement(
                        workspace_id=current_user.workspace_id,
                        product_id=item.product_id,
                        warehouse_id=order.warehouse_id,
                        destination_warehouse_id=None,
                        movement_type="reservation_release",
                        quantity=item.quantity,
                        quantity_before=before_reserved,
                        quantity_after=new_reserved,
                        reason="order_cancellation",
                        reference_type="order",
                        reference_id=order.id,
                        notes=f"Released reservation for {order.order_number}",
                        created_by=current_user.user_id,
                    )
                    product = self.inventory_repository.get_product(current_user.workspace_id, item.product_id)
                    warehouse = self.inventory_repository.get_warehouse(current_user.workspace_id, order.warehouse_id)
                    self._sync_low_stock_alert(
                        product,
                        warehouse,
                        balance["on_hand_quantity"],
                        new_reserved,
                        current_user.user_id,
                    )
            self.order_repository.update_order_header(
                current_user.workspace_id,
                order_id,
                {"status": "cancelled", "cancelled_at": self._sql_now_marker()},
            )
            self.activity_repository.create_log(
                workspace_id=current_user.workspace_id,
                actor_user_id=current_user.user_id,
                action="order.cancelled",
                entity_type="order",
                entity_id=order.id,
                summary=f"Cancelled order {order.order_number}",
            )
            self._resolve_stale_order_alert(current_user.workspace_id, order_id, current_user.user_id)
        return self.get_order(current_user, order_id)

    def _validate_order_payload(self, workspace_id: str, payload: dict) -> None:
        if not self.order_repository.warehouse_exists(workspace_id, payload["warehouse_id"]):
            raise ValidationAppError("Selected warehouse does not exist.")
        if payload["order_type"] == "purchase" and not self.order_repository.supplier_exists(workspace_id, payload["supplier_id"]):
            raise ValidationAppError("Selected supplier does not exist.")
        product_ids = [item["product_id"] for item in payload["items"]]
        if len(product_ids) != len(set(product_ids)):
            raise ValidationAppError("Duplicate products are not allowed in the same order.")
        rows = self.order_repository.products_for_ids(workspace_id, product_ids)
        if len(rows) != len(product_ids):
            raise ValidationAppError("One or more order items reference an unknown product.")

    def _calculate_subtotal(self, payload: dict) -> float:
        return float(sum(self._line_total(payload["order_type"], item) for item in payload["items"]))

    def _line_total(self, order_type: str, item: dict) -> float:
        unit_value = item.get("unit_price") if order_type == "sales" else item.get("unit_cost")
        if unit_value is None:
            raise ValidationAppError("Each order item must include a unit price or unit cost.")
        return round(float(unit_value) * int(item["quantity"]), 2)

    def _reserve_sales_order_stock(self, current_user: CurrentUser, order: OrderDetailResponse) -> None:
        product_counts = Counter(item.product_id for item in order.items)
        if any(count > 1 for count in product_counts.values()):
            raise ValidationAppError("Duplicate products are not allowed in a sales order.")
        for item in order.items:
            balance = self.inventory_repository.get_balance_for_update(current_user.workspace_id, item.product_id, order.warehouse_id)
            if not balance:
                raise InsufficientStockError()
            available = balance["on_hand_quantity"] - balance["reserved_quantity"]
            if item.quantity > available:
                raise InsufficientStockError(f"Not enough available stock for product {item.product_name}.")
            before_reserved = balance["reserved_quantity"]
            after_reserved = before_reserved + item.quantity
            self.inventory_repository.update_balance(
                balance_id=balance["id"],
                on_hand_quantity=balance["on_hand_quantity"],
                reserved_quantity=after_reserved,
            )
            self.inventory_repository.insert_movement(
                workspace_id=current_user.workspace_id,
                product_id=item.product_id,
                warehouse_id=order.warehouse_id,
                destination_warehouse_id=None,
                movement_type="reservation",
                quantity=item.quantity,
                quantity_before=before_reserved,
                quantity_after=after_reserved,
                reason="sales_order_confirmation",
                reference_type="order",
                reference_id=order.id,
                notes=f"Reserved stock for {order.order_number}",
                created_by=current_user.user_id,
            )

    def _sync_low_stock_alert(self, product: dict | None, warehouse: dict | None, on_hand_quantity: int, reserved_quantity: int, actor_user_id: str | None) -> None:
        if not product or not warehouse:
            return
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

    def _resolve_stale_order_alert(self, workspace_id: str, order_id: str, actor_user_id: str | None) -> None:
        self.alert_repository.resolve_open_alert(
            workspace_id=workspace_id,
            alert_type="stale_order",
            order_id=order_id,
            resolved_by=actor_user_id,
        )
        self.alert_repository.resolve_open_alert(
            workspace_id=workspace_id,
            alert_type="stuck_processing",
            order_id=order_id,
            resolved_by=actor_user_id,
        )

    def _sql_now_marker(self):
        from datetime import datetime, UTC
        return datetime.now(UTC)
