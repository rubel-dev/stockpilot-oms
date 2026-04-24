from app.core.exceptions import ConflictError, NotFoundError
from app.core.pagination import normalize_pagination
from app.repositories.activity_repository import ActivityRepository
from app.repositories.warehouse_repository import WarehouseRepository
from app.schemas.warehouse import WarehouseDetailResponse, WarehouseListResponse
from app.services.auth_service import CurrentUser


class WarehouseService:
    def __init__(
        self,
        warehouse_repository: WarehouseRepository,
        activity_repository: ActivityRepository,
    ) -> None:
        self.warehouse_repository = warehouse_repository
        self.activity_repository = activity_repository

    def list_warehouses(
        self,
        current_user: CurrentUser,
        *,
        page: int,
        page_size: int,
        search: str | None,
        status: str | None,
        sort: str,
        direction: str,
    ) -> WarehouseListResponse:
        pagination = normalize_pagination(page, page_size)
        safe_sort = sort if sort in self.warehouse_repository.SORT_FIELDS else "updated_at"
        safe_direction = direction.lower() if direction.lower() in {"asc", "desc"} else "desc"
        items = self.warehouse_repository.list_warehouses(
            workspace_id=current_user.workspace_id,
            pagination_offset=pagination.offset,
            page_size=pagination.page_size,
            search=search.strip() if search else None,
            status=status,
            sort_field=safe_sort,
            sort_direction=safe_direction,
        )
        total = self.warehouse_repository.count_warehouses(
            workspace_id=current_user.workspace_id,
            search=search.strip() if search else None,
            status=status,
        )
        return WarehouseListResponse(
            items=items,
            page=pagination.page,
            page_size=pagination.page_size,
            total=total,
        )

    def get_warehouse(self, current_user: CurrentUser, warehouse_id: str) -> WarehouseDetailResponse:
        row = self.warehouse_repository.get_warehouse_detail(current_user.workspace_id, warehouse_id)
        if not row:
            raise NotFoundError("Warehouse not found.")
        return WarehouseDetailResponse(**row)

    def create_warehouse(self, current_user: CurrentUser, payload: dict) -> WarehouseDetailResponse:
        code = payload["code"].strip().upper()
        if self.warehouse_repository.code_exists(current_user.workspace_id, code):
            raise ConflictError("A warehouse with this code already exists in the workspace.")
        with self.warehouse_repository.connection.transaction():
            created = self.warehouse_repository.create_warehouse(
                {
                    "workspace_id": current_user.workspace_id,
                    "name": payload["name"].strip(),
                    "code": code,
                    "address_line1": payload.get("address_line1"),
                    "address_line2": payload.get("address_line2"),
                    "city": payload.get("city"),
                    "state_region": payload.get("state_region"),
                    "postal_code": payload.get("postal_code"),
                    "country": payload.get("country"),
                }
            )
            self.activity_repository.create_log(
                workspace_id=current_user.workspace_id,
                actor_user_id=current_user.user_id,
                action="warehouse.created",
                entity_type="warehouse",
                entity_id=created["id"],
                summary=f"Created warehouse {payload['name'].strip()}",
                metadata={"code": code},
            )
        return self.get_warehouse(current_user, created["id"])

    def update_warehouse(self, current_user: CurrentUser, warehouse_id: str, payload: dict) -> WarehouseDetailResponse:
        existing = self.warehouse_repository.get_warehouse_detail(current_user.workspace_id, warehouse_id)
        if not existing:
            raise NotFoundError("Warehouse not found.")

        fields: dict[str, object] = {}
        for key in [
            "name",
            "address_line1",
            "address_line2",
            "city",
            "state_region",
            "postal_code",
            "country",
            "status",
        ]:
            if key in payload and payload[key] is not None:
                fields[key] = payload[key].strip() if isinstance(payload[key], str) else payload[key]

        if payload.get("code") is not None:
            code = payload["code"].strip().upper()
            if self.warehouse_repository.code_exists(
                current_user.workspace_id,
                code,
                exclude_warehouse_id=warehouse_id,
            ):
                raise ConflictError("A warehouse with this code already exists in the workspace.")
            fields["code"] = code

        if not fields:
            return WarehouseDetailResponse(**existing)

        with self.warehouse_repository.connection.transaction():
            self.warehouse_repository.update_warehouse(current_user.workspace_id, warehouse_id, fields)
            self.activity_repository.create_log(
                workspace_id=current_user.workspace_id,
                actor_user_id=current_user.user_id,
                action="warehouse.updated",
                entity_type="warehouse",
                entity_id=warehouse_id,
                summary=f"Updated warehouse {existing['name']}",
            )
        return self.get_warehouse(current_user, warehouse_id)
