from psycopg import Connection
from psycopg.sql import SQL

from app.repositories.sql_utils import build_update_statement


class WarehouseRepository:
    UPDATABLE_FIELDS = {
        "name",
        "code",
        "address_line1",
        "address_line2",
        "city",
        "state_region",
        "postal_code",
        "country",
        "status",
    }

    SORT_FIELDS = {
        "name": SQL("w.name"),
        "code": SQL("w.code"),
        "created_at": SQL("w.created_at"),
        "updated_at": SQL("w.updated_at"),
    }

    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def code_exists(self, workspace_id: str, code: str, exclude_warehouse_id: str | None = None) -> bool:
        query = """
            SELECT 1
            FROM warehouses
            WHERE workspace_id = %s
              AND code = %s
              AND (%s::uuid IS NULL OR id <> %s::uuid)
            LIMIT 1
        """
        return (
            self.connection.execute(query, (workspace_id, code, exclude_warehouse_id, exclude_warehouse_id)).fetchone()
            is not None
        )

    def create_warehouse(self, payload: dict[str, object]) -> dict:
        query = """
            INSERT INTO warehouses (
                workspace_id,
                name,
                code,
                address_line1,
                address_line2,
                city,
                state_region,
                postal_code,
                country
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id::text
        """
        return self.connection.execute(
            query,
            (
                payload["workspace_id"],
                payload["name"],
                payload["code"],
                payload["address_line1"],
                payload["address_line2"],
                payload["city"],
                payload["state_region"],
                payload["postal_code"],
                payload["country"],
            ),
        ).fetchone()

    def get_warehouse_detail(self, workspace_id: str, warehouse_id: str) -> dict | None:
        query = """
            SELECT
                w.id::text,
                w.workspace_id::text,
                w.name,
                w.code,
                w.address_line1,
                w.address_line2,
                w.city,
                w.state_region,
                w.postal_code,
                w.country,
                w.status,
                COUNT(DISTINCT ib.product_id) AS total_skus,
                COALESCE(SUM(ib.on_hand_quantity), 0) AS total_units,
                COALESCE(SUM(ib.reserved_quantity), 0) AS total_reserved,
                COUNT(DISTINCT CASE
                    WHEN (ib.on_hand_quantity - ib.reserved_quantity) <= p.reorder_point THEN ib.product_id
                    ELSE NULL
                END) AS low_stock_items,
                w.created_at,
                w.updated_at
            FROM warehouses w
            LEFT JOIN inventory_balances ib
                ON ib.warehouse_id = w.id
               AND ib.workspace_id = w.workspace_id
            LEFT JOIN products p
                ON p.id = ib.product_id
               AND p.workspace_id = ib.workspace_id
            WHERE w.workspace_id = %s
              AND w.id = %s
            GROUP BY w.id
            LIMIT 1
        """
        return self.connection.execute(query, (workspace_id, warehouse_id)).fetchone()

    def list_warehouses(
        self,
        *,
        workspace_id: str,
        pagination_offset: int,
        page_size: int,
        search: str | None,
        status: str | None,
        sort_field: str,
        sort_direction: str,
    ) -> list[dict]:
        search_pattern = f"%{search}%" if search else None
        order_clause = SQL(" ORDER BY {} {} ").format(
            self.SORT_FIELDS[sort_field],
            SQL("DESC" if sort_direction == "desc" else "ASC"),
        )
        base_query = SQL(
            """
            SELECT
                w.id::text,
                w.workspace_id::text,
                w.name,
                w.code,
                w.city,
                w.country,
                w.status,
                COUNT(DISTINCT ib.product_id) AS total_skus,
                COALESCE(SUM(ib.on_hand_quantity), 0) AS total_units,
                COALESCE(SUM(ib.reserved_quantity), 0) AS total_reserved,
                COUNT(DISTINCT CASE
                    WHEN (ib.on_hand_quantity - ib.reserved_quantity) <= p.reorder_point THEN ib.product_id
                    ELSE NULL
                END) AS low_stock_items,
                w.created_at,
                w.updated_at
            FROM warehouses w
            LEFT JOIN inventory_balances ib
                ON ib.warehouse_id = w.id
               AND ib.workspace_id = w.workspace_id
            LEFT JOIN products p
                ON p.id = ib.product_id
               AND p.workspace_id = ib.workspace_id
            WHERE w.workspace_id = %s
              AND (%s::text IS NULL OR w.status = %s)
              AND (
                    %s::text IS NULL
                    OR w.name ILIKE %s
                    OR w.code ILIKE %s
                    OR COALESCE(w.city, '') ILIKE %s
                    OR COALESCE(w.country, '') ILIKE %s
              )
            GROUP BY w.id
            """
        ) + order_clause + SQL(" LIMIT %s OFFSET %s ")
        params = (
            workspace_id,
            status,
            status,
            search,
            search_pattern,
            search_pattern,
            search_pattern,
            search_pattern,
            page_size,
            pagination_offset,
        )
        return list(self.connection.execute(base_query, params).fetchall())

    def count_warehouses(self, *, workspace_id: str, search: str | None, status: str | None) -> int:
        search_pattern = f"%{search}%" if search else None
        query = """
            SELECT COUNT(*) AS total
            FROM warehouses w
            WHERE w.workspace_id = %s
              AND (%s::text IS NULL OR w.status = %s)
              AND (
                    %s::text IS NULL
                    OR w.name ILIKE %s
                    OR w.code ILIKE %s
                    OR COALESCE(w.city, '') ILIKE %s
                    OR COALESCE(w.country, '') ILIKE %s
              )
        """
        row = self.connection.execute(
            query,
            (workspace_id, status, status, search, search_pattern, search_pattern, search_pattern, search_pattern),
        ).fetchone()
        return int(row["total"])

    def update_warehouse(self, workspace_id: str, warehouse_id: str, fields: dict[str, object]) -> None:
        set_parts, params = build_update_statement(fields=fields, allowed_fields=self.UPDATABLE_FIELDS)
        params.extend([workspace_id, warehouse_id])
        query = SQL("""
            UPDATE warehouses
            SET {},
                updated_at = NOW()
            WHERE workspace_id = %s
              AND id = %s
        """).format(set_parts)
        self.connection.execute(query, params)
