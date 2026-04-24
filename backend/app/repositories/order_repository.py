from datetime import UTC, datetime

from psycopg import Connection
from psycopg.sql import SQL

from app.repositories.sql_utils import build_update_statement


class OrderRepository:
    UPDATABLE_FIELDS = {
        "status",
        "supplier_id",
        "customer_name",
        "notes",
        "subtotal_amount",
        "confirmed_at",
        "processed_at",
        "shipped_at",
        "completed_at",
        "cancelled_at",
    }

    SORT_FIELDS = {
        "created_at": "o.created_at",
        "updated_at": "o.updated_at",
        "order_number": "o.order_number",
        "status": "o.status",
    }

    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def warehouse_exists(self, workspace_id: str, warehouse_id: str) -> bool:
        row = self.connection.execute(
            "SELECT 1 FROM warehouses WHERE workspace_id = %s AND id = %s LIMIT 1",
            (workspace_id, warehouse_id),
        ).fetchone()
        return row is not None

    def supplier_exists(self, workspace_id: str, supplier_id: str) -> bool:
        row = self.connection.execute(
            "SELECT 1 FROM suppliers WHERE workspace_id = %s AND id = %s LIMIT 1",
            (workspace_id, supplier_id),
        ).fetchone()
        return row is not None

    def supplier_product_exists(self, workspace_id: str, supplier_id: str, product_id: str) -> bool:
        row = self.connection.execute(
            """
            SELECT 1 FROM supplier_products
            WHERE workspace_id = %s AND supplier_id = %s AND product_id = %s
            LIMIT 1
            """,
            (workspace_id, supplier_id, product_id),
        ).fetchone()
        return row is not None

    def products_for_ids(self, workspace_id: str, product_ids: list[str]) -> list[dict]:
        query = """
            SELECT id::text, name, sku
            FROM products
            WHERE workspace_id = %s
              AND id = ANY(%s::uuid[])
        """
        return list(self.connection.execute(query, (workspace_id, product_ids)).fetchall())

    def next_order_number(self, workspace_id: str, order_type: str) -> str:
        prefix = "SO" if order_type == "sales" else "PO"
        year = datetime.now(UTC).year
        self.connection.execute(
            "SELECT pg_advisory_xact_lock(hashtext(%s))",
            (f"{workspace_id}:{order_type}:{year}",),
        )
        query = """
            SELECT
                COALESCE(
                    MAX(
                        CASE
                            WHEN order_number ~ %s THEN split_part(order_number, '-', 3)::int
                            ELSE 0
                        END
                    ),
                    0
                ) + 1 AS next_number
            FROM orders
            WHERE workspace_id = %s
              AND order_type = %s
              AND order_number LIKE %s
        """
        row = self.connection.execute(
            query,
            (rf"^{prefix}-{year}-\d{{4,}}$", workspace_id, order_type, f"{prefix}-{year}-%"),
        ).fetchone()
        return f"{prefix}-{year}-{int(row['next_number']):04d}"

    def create_order(self, payload: dict) -> dict:
        query = """
            INSERT INTO orders (
                workspace_id, order_number, order_type, status, warehouse_id, supplier_id,
                customer_name, notes, subtotal_amount, created_by
            )
            VALUES (%s, %s, %s, 'draft', %s, %s, %s, %s, %s, %s)
            RETURNING id::text
        """
        return self.connection.execute(
            query,
            (
                payload["workspace_id"],
                payload["order_number"],
                payload["order_type"],
                payload["warehouse_id"],
                payload.get("supplier_id"),
                payload.get("customer_name"),
                payload.get("notes"),
                payload["subtotal_amount"],
                payload["created_by"],
            ),
        ).fetchone()

    def insert_order_item(self, payload: dict) -> None:
        query = """
            INSERT INTO order_items (
                workspace_id, order_id, product_id, quantity, unit_price, unit_cost, line_total
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        self.connection.execute(
            query,
            (
                payload["workspace_id"],
                payload["order_id"],
                payload["product_id"],
                payload["quantity"],
                payload.get("unit_price"),
                payload.get("unit_cost"),
                payload["line_total"],
            ),
        )

    def replace_order_items(self, workspace_id: str, order_id: str, items: list[dict]) -> None:
        self.connection.execute(
            "DELETE FROM order_items WHERE workspace_id = %s AND order_id = %s",
            (workspace_id, order_id),
        )
        for item in items:
            self.insert_order_item(
                {
                    "workspace_id": workspace_id,
                    "order_id": order_id,
                    **item,
                }
            )

    def get_order_detail(self, workspace_id: str, order_id: str) -> dict | None:
        query = """
            SELECT
                o.id::text,
                o.workspace_id::text,
                o.order_number,
                o.order_type,
                o.status,
                o.warehouse_id::text,
                w.name AS warehouse_name,
                o.supplier_id::text,
                s.name AS supplier_name,
                o.customer_name,
                o.notes,
                o.subtotal_amount::float8 AS subtotal_amount,
                o.created_by::text,
                o.confirmed_at,
                o.processed_at,
                o.shipped_at,
                o.completed_at,
                o.cancelled_at,
                o.created_at,
                o.updated_at
            FROM orders o
            JOIN warehouses w
              ON w.id = o.warehouse_id AND w.workspace_id = o.workspace_id
            LEFT JOIN suppliers s
              ON s.id = o.supplier_id AND s.workspace_id = o.workspace_id
            WHERE o.workspace_id = %s
              AND o.id = %s
            LIMIT 1
        """
        return self.connection.execute(query, (workspace_id, order_id)).fetchone()

    def list_order_items(self, workspace_id: str, order_id: str) -> list[dict]:
        query = """
            SELECT
                oi.id::text,
                oi.product_id::text,
                p.name AS product_name,
                p.sku AS product_sku,
                oi.quantity,
                oi.unit_price::float8 AS unit_price,
                oi.unit_cost::float8 AS unit_cost,
                oi.line_total::float8 AS line_total,
                oi.created_at,
                oi.updated_at
            FROM order_items oi
            JOIN products p
              ON p.id = oi.product_id AND p.workspace_id = oi.workspace_id
            WHERE oi.workspace_id = %s
              AND oi.order_id = %s
            ORDER BY oi.created_at ASC
        """
        return list(self.connection.execute(query, (workspace_id, order_id)).fetchall())

    def list_orders(
        self,
        *,
        workspace_id: str,
        page_size: int,
        offset: int,
        order_type: str | None,
        status: str | None,
        supplier_id: str | None,
        warehouse_id: str | None,
        search: str | None,
        sort_field: str,
        sort_direction: str,
    ) -> list[dict]:
        search_pattern = f"%{search}%" if search else None
        order = self.SORT_FIELDS.get(sort_field, "o.updated_at")
        direction = "DESC" if sort_direction == "desc" else "ASC"
        query = f"""
            SELECT
                o.id::text,
                o.workspace_id::text,
                o.order_number,
                o.order_type,
                o.status,
                o.warehouse_id::text,
                w.name AS warehouse_name,
                o.supplier_id::text,
                s.name AS supplier_name,
                o.customer_name,
                COUNT(oi.id) AS item_count,
                o.subtotal_amount::float8 AS subtotal_amount,
                o.created_at,
                o.updated_at
            FROM orders o
            JOIN warehouses w
              ON w.id = o.warehouse_id AND w.workspace_id = o.workspace_id
            LEFT JOIN suppliers s
              ON s.id = o.supplier_id AND s.workspace_id = o.workspace_id
            LEFT JOIN order_items oi
              ON oi.order_id = o.id AND oi.workspace_id = o.workspace_id
            WHERE o.workspace_id = %s
              AND (%s::text IS NULL OR o.order_type = %s)
              AND (%s::text IS NULL OR o.status = %s)
              AND (%s::uuid IS NULL OR o.supplier_id = %s::uuid)
              AND (%s::uuid IS NULL OR o.warehouse_id = %s::uuid)
              AND (
                    %s::text IS NULL
                    OR o.order_number ILIKE %s
                    OR COALESCE(o.customer_name, '') ILIKE %s
                    OR COALESCE(s.name, '') ILIKE %s
              )
            GROUP BY o.id, w.name, s.name
            ORDER BY {order} {direction}
            LIMIT %s OFFSET %s
        """
        return list(
            self.connection.execute(
                query,
                (
                    workspace_id,
                    order_type,
                    order_type,
                    status,
                    status,
                    supplier_id,
                    supplier_id,
                    warehouse_id,
                    warehouse_id,
                    search,
                    search_pattern,
                    search_pattern,
                    search_pattern,
                    page_size,
                    offset,
                ),
            ).fetchall()
        )

    def count_orders(
        self,
        *,
        workspace_id: str,
        order_type: str | None,
        status: str | None,
        supplier_id: str | None,
        warehouse_id: str | None,
        search: str | None,
    ) -> int:
        search_pattern = f"%{search}%" if search else None
        query = """
            SELECT COUNT(*) AS total
            FROM orders o
            LEFT JOIN suppliers s
              ON s.id = o.supplier_id AND s.workspace_id = o.workspace_id
            WHERE o.workspace_id = %s
              AND (%s::text IS NULL OR o.order_type = %s)
              AND (%s::text IS NULL OR o.status = %s)
              AND (%s::uuid IS NULL OR o.supplier_id = %s::uuid)
              AND (%s::uuid IS NULL OR o.warehouse_id = %s::uuid)
              AND (
                    %s::text IS NULL
                    OR o.order_number ILIKE %s
                    OR COALESCE(o.customer_name, '') ILIKE %s
                    OR COALESCE(s.name, '') ILIKE %s
              )
        """
        row = self.connection.execute(
            query,
            (
                workspace_id,
                order_type,
                order_type,
                status,
                status,
                supplier_id,
                supplier_id,
                warehouse_id,
                warehouse_id,
                search,
                search_pattern,
                search_pattern,
                search_pattern,
            ),
        ).fetchone()
        return int(row["total"])

    def update_order_header(self, workspace_id: str, order_id: str, fields: dict[str, object]) -> None:
        set_parts, params = build_update_statement(fields=fields, allowed_fields=self.UPDATABLE_FIELDS)
        params.extend([workspace_id, order_id])
        query = SQL("""
            UPDATE orders
            SET {},
                updated_at = NOW()
            WHERE workspace_id = %s
              AND id = %s
        """).format(set_parts)
        self.connection.execute(query, params)
