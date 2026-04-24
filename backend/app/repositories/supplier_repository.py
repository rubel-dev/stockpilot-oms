from psycopg import Connection


class SupplierRepository:
    SORT_FIELDS = {
        "name": "s.name",
        "created_at": "s.created_at",
        "updated_at": "s.updated_at",
    }

    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def create_supplier(self, payload: dict) -> dict:
        query = """
            INSERT INTO suppliers (workspace_id, name, contact_name, email, phone, address, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id::text
        """
        return self.connection.execute(
            query,
            (
                payload["workspace_id"],
                payload["name"],
                payload["contact_name"],
                payload["email"],
                payload["phone"],
                payload["address"],
                payload["notes"],
            ),
        ).fetchone()

    def update_supplier(self, workspace_id: str, supplier_id: str, fields: dict[str, object]) -> None:
        params = list(fields.values()) + [workspace_id, supplier_id]
        query = f"""
            UPDATE suppliers
            SET {", ".join(f"{key} = %s" for key in fields)},
                updated_at = NOW()
            WHERE workspace_id = %s
              AND id = %s
        """
        self.connection.execute(query, params)

    def get_supplier_detail(self, workspace_id: str, supplier_id: str) -> dict | None:
        query = """
            SELECT
                s.id::text,
                s.workspace_id::text,
                s.name,
                s.contact_name,
                s.email,
                s.phone,
                s.address,
                s.status,
                s.notes,
                COUNT(DISTINCT sp.product_id) AS active_product_count,
                MAX(CASE WHEN o.order_type = 'purchase' AND o.status = 'completed' THEN o.completed_at ELSE NULL END) AS last_restock_at,
                s.created_at,
                s.updated_at
            FROM suppliers s
            LEFT JOIN supplier_products sp
              ON sp.supplier_id = s.id
             AND sp.workspace_id = s.workspace_id
            LEFT JOIN orders o
              ON o.supplier_id = s.id
             AND o.workspace_id = s.workspace_id
            WHERE s.workspace_id = %s
              AND s.id = %s
            GROUP BY s.id
            LIMIT 1
        """
        return self.connection.execute(query, (workspace_id, supplier_id)).fetchone()

    def list_supplier_links(self, workspace_id: str, supplier_id: str) -> list[dict]:
        query = """
            SELECT
                sp.id::text,
                sp.product_id::text,
                p.name AS product_name,
                p.sku AS product_sku,
                sp.supplier_sku,
                sp.lead_time_days,
                sp.minimum_order_quantity,
                sp.unit_cost::float8 AS unit_cost,
                sp.is_preferred,
                sp.created_at,
                sp.updated_at
            FROM supplier_products sp
            JOIN products p
              ON p.id = sp.product_id
             AND p.workspace_id = sp.workspace_id
            WHERE sp.workspace_id = %s
              AND sp.supplier_id = %s
            ORDER BY p.name ASC
        """
        return list(self.connection.execute(query, (workspace_id, supplier_id)).fetchall())

    def list_suppliers(
        self,
        *,
        workspace_id: str,
        page_size: int,
        offset: int,
        search: str | None,
        status: str | None,
        sort_field: str,
        sort_direction: str,
    ) -> list[dict]:
        search_pattern = f"%{search}%" if search else None
        order = self.SORT_FIELDS.get(sort_field, "s.updated_at")
        direction = "DESC" if sort_direction == "desc" else "ASC"
        query = f"""
            SELECT
                s.id::text,
                s.workspace_id::text,
                s.name,
                s.contact_name,
                s.email,
                s.phone,
                s.status,
                COUNT(DISTINCT sp.product_id) AS active_product_count,
                MAX(CASE WHEN o.order_type = 'purchase' AND o.status = 'completed' THEN o.completed_at ELSE NULL END) AS last_restock_at,
                s.created_at,
                s.updated_at
            FROM suppliers s
            LEFT JOIN supplier_products sp
              ON sp.supplier_id = s.id
             AND sp.workspace_id = s.workspace_id
            LEFT JOIN orders o
              ON o.supplier_id = s.id
             AND o.workspace_id = s.workspace_id
            WHERE s.workspace_id = %s
              AND (%s::text IS NULL OR s.status = %s)
              AND (
                    %s::text IS NULL
                    OR s.name ILIKE %s
                    OR COALESCE(s.contact_name, '') ILIKE %s
                    OR COALESCE(s.email, '') ILIKE %s
              )
            GROUP BY s.id
            ORDER BY {order} {direction}
            LIMIT %s OFFSET %s
        """
        return list(
            self.connection.execute(
                query,
                (
                    workspace_id,
                    status,
                    status,
                    search,
                    search_pattern,
                    search_pattern,
                    search_pattern,
                    page_size,
                    offset,
                ),
            ).fetchall()
        )

    def count_suppliers(self, *, workspace_id: str, search: str | None, status: str | None) -> int:
        search_pattern = f"%{search}%" if search else None
        query = """
            SELECT COUNT(*) AS total
            FROM suppliers s
            WHERE s.workspace_id = %s
              AND (%s::text IS NULL OR s.status = %s)
              AND (
                    %s::text IS NULL
                    OR s.name ILIKE %s
                    OR COALESCE(s.contact_name, '') ILIKE %s
                    OR COALESCE(s.email, '') ILIKE %s
              )
        """
        row = self.connection.execute(
            query,
            (workspace_id, status, status, search, search_pattern, search_pattern, search_pattern),
        ).fetchone()
        return int(row["total"])

    def product_exists(self, workspace_id: str, product_id: str) -> bool:
        row = self.connection.execute(
            "SELECT 1 FROM products WHERE workspace_id = %s AND id = %s LIMIT 1",
            (workspace_id, product_id),
        ).fetchone()
        return row is not None

    def link_product(self, *, workspace_id: str, supplier_id: str, payload: dict) -> dict:
        query = """
            INSERT INTO supplier_products (
                workspace_id, supplier_id, product_id, supplier_sku, lead_time_days,
                minimum_order_quantity, unit_cost, is_preferred
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id::text
        """
        return self.connection.execute(
            query,
            (
                workspace_id,
                supplier_id,
                payload["product_id"],
                payload.get("supplier_sku"),
                payload.get("lead_time_days"),
                payload.get("minimum_order_quantity", 0),
                payload.get("unit_cost"),
                payload.get("is_preferred", False),
            ),
        ).fetchone()

    def unlink_product(self, workspace_id: str, supplier_id: str, product_id: str) -> bool:
        row = self.connection.execute(
            """
            DELETE FROM supplier_products
            WHERE workspace_id = %s
              AND supplier_id = %s
              AND product_id = %s
            RETURNING id
            """,
            (workspace_id, supplier_id, product_id),
        ).fetchone()
        return row is not None

    def supplier_product_exists(self, workspace_id: str, supplier_id: str, product_id: str) -> bool:
        row = self.connection.execute(
            """
            SELECT 1
            FROM supplier_products
            WHERE workspace_id = %s
              AND supplier_id = %s
              AND product_id = %s
            LIMIT 1
            """,
            (workspace_id, supplier_id, product_id),
        ).fetchone()
        return row is not None

