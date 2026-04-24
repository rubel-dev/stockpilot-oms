from app.core.exceptions import NotFoundError
from app.core.pagination import normalize_pagination
from app.repositories.activity_repository import ActivityRepository
from app.repositories.alert_repository import AlertRepository
from app.repositories.order_repository import OrderRepository
from app.schemas.alert import AlertListResponse, AlertSummaryResponse
from app.services.auth_service import CurrentUser


class AlertService:
    def __init__(self, alert_repository: AlertRepository, order_repository: OrderRepository, activity_repository: ActivityRepository) -> None:
        self.alert_repository = alert_repository
        self.order_repository = order_repository
        self.activity_repository = activity_repository

    def list_alerts(self, current_user: CurrentUser, *, page: int, page_size: int, alert_type: str | None, severity: str | None, status: str | None, warehouse_id: str | None, product_id: str | None) -> AlertListResponse:
        pagination = normalize_pagination(page, page_size)
        items = self.alert_repository.list_alerts(
            workspace_id=current_user.workspace_id,
            page_size=pagination.page_size,
            offset=pagination.offset,
            alert_type=alert_type,
            severity=severity,
            status=status,
            warehouse_id=warehouse_id,
            product_id=product_id,
        )
        total = self.alert_repository.count_alerts(
            workspace_id=current_user.workspace_id,
            alert_type=alert_type,
            severity=severity,
            status=status,
            warehouse_id=warehouse_id,
            product_id=product_id,
        )
        return AlertListResponse(items=items, page=pagination.page, page_size=pagination.page_size, total=total)

    def summary(self, current_user: CurrentUser) -> AlertSummaryResponse:
        return AlertSummaryResponse(items=self.alert_repository.summary(current_user.workspace_id))

    def resolve(self, current_user: CurrentUser, alert_id: str):
        with self.alert_repository.connection.transaction():
            row = self.alert_repository.resolve_alert_by_id(current_user.workspace_id, alert_id, current_user.user_id)
            if not row:
                raise NotFoundError("Alert not found.")
            self.activity_repository.create_log(
                workspace_id=current_user.workspace_id,
                actor_user_id=current_user.user_id,
                action="alert.resolved",
                entity_type="alert",
                entity_id=alert_id,
                summary=f"Resolved alert {alert_id}",
            )
            return row

    def dismiss(self, current_user: CurrentUser, alert_id: str):
        with self.alert_repository.connection.transaction():
            row = self.alert_repository.dismiss_alert(current_user.workspace_id, alert_id, current_user.user_id)
            if not row:
                raise NotFoundError("Alert not found.")
            self.activity_repository.create_log(
                workspace_id=current_user.workspace_id,
                actor_user_id=current_user.user_id,
                action="alert.dismissed",
                entity_type="alert",
                entity_id=alert_id,
                summary=f"Dismissed alert {alert_id}",
            )
            return row

    def recalculate(self, current_user: CurrentUser) -> AlertSummaryResponse:
        with self.alert_repository.connection.transaction():
            processing_orders = self.order_repository.list_orders(
                workspace_id=current_user.workspace_id,
                page_size=200,
                offset=0,
                order_type=None,
                status="processing",
                supplier_id=None,
                warehouse_id=None,
                search=None,
                sort_field="updated_at",
                sort_direction="desc",
            )
            for order in processing_orders:
                existing = self.alert_repository.find_open_alert(
                    workspace_id=current_user.workspace_id,
                    alert_type="stuck_processing",
                    order_id=order["id"],
                )
                if not existing:
                    self.alert_repository.create_alert(
                        workspace_id=current_user.workspace_id,
                        alert_type="stuck_processing",
                        severity="warning",
                        product_id=None,
                        warehouse_id=order["warehouse_id"],
                        order_id=order["id"],
                        title=f"Order {order['order_number']} is still processing",
                        message=f"{order['order_number']} has remained in processing and should be reviewed.",
                        metadata={"order_number": order["order_number"]},
                    )
            self.activity_repository.create_log(
                workspace_id=current_user.workspace_id,
                actor_user_id=current_user.user_id,
                action="alert.recalculated",
                entity_type="alert",
                entity_id=None,
                summary="Recalculated operational alerts",
            )
        return self.summary(current_user)

