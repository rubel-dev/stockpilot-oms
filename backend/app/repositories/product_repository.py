from psycopg import Connection
from psycopg.sql import SQL

from app.repositories.sql_utils import build_update_statement


class ProductRepository:
    UPDATABLE_FIELDS = {
        "name",
        "category_id",
        "description",
        "unit",
        "reorder_point",
        "reorder_quantity",
        "status",
        "sku",
    }

    SORT_FIELDS = {
        "name": SQL("p.name"),
        "sku": SQL("p.sku"),
        "created_at": SQL("p.created_at"),
        "updated_at": SQL("p.updated_at"),
    }

    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def category_exists(self, workspace_id: str, category_id: str) -> bool:
        query = """
            SELECT 1
            FROM categories
            WHERE id = %s
              AND workspace_id = %s
            LIMIT 1
        """
        return self.connection.execute(query, (category_id, workspace_id)).fetchone() is not None

    def sku_exists(self, workspace_id: str, sku: str, exclude_product_id: str | None = None) -> bool:
        query = """
            SELECT 1
            FROM products
            WHERE workspace_id = %s
              AND sku = %s
              AND (%s::uuid IS NULL OR id <> %s::uuid)
            LIMIT 1
        """
        return (
            self.connection.execute(query, (workspace_id, sku, exclude_product_id, exclude_product_id)).fetchone()
            is not None
        )

    def create_product(self, payload: dict[str, object]) -> dict:
        query = """
            INSERT INTO products (
                workspace_id,
                category_id,
                name,
                sku,
                description,
                unit,
                reorder_point,
                reorder_quantity,
                created_by
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id::text
        """
        return self.connection.execute(
            query,
            (
                payload["workspace_id"],
                payload["category_id"],
                payload["name"],
                payload["sku"],
                payload["description"],
                payload["unit"],
                payload["reorder_point"],
                payload["reorder_quantity"],
                payload["created_by"],
            ),
        ).fetchone()

    def get_product_detail(self, workspace_id: str, product_id: str) -> dict | None:
        query = """
            SELECT
                p.id::text,
                p.workspace_id::text,
                p.category_id::text,
                c.name AS category_name,
                p.name,
                p.sku,
                p.description,
                p.unit,
                p.reorder_point,
                p.reorder_quantity,
                p.status,
                p.created_by::text,
                COALESCE(SUM(ib.on_hand_quantity), 0) AS total_on_hand,
                COALESCE(SUM(ib.reserved_quantity), 0) AS total_reserved,
                COALESCE(SUM(ib.on_hand_quantity - ib.reserved_quantity), 0) AS total_available,
                COUNT(DISTINCT ib.warehouse_id) AS warehouse_count,
                p.created_at,
                p.updated_at
            FROM products p
            LEFT JOIN categories c
                ON c.id = p.category_id
               AND c.workspace_id = p.workspace_id
            LEFT JOIN inventory_balances ib
                ON ib.product_id = p.id
               AND ib.workspace_id = p.workspace_id
            WHERE p.workspace_id = %s
              AND p.id = %s
            GROUP BY p.id, c.name
            LIMIT 1
        """
        return self.connection.execute(query, (workspace_id, product_id)).fetchone()

    def list_products(
        self,
        *,
        workspace_id: str,
        pagination_offset: int,
        page_size: int,
        search: str | None,
        category_id: str | None,
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
                p.id::text,
                p.workspace_id::text,
                p.category_id::text,
                c.name AS category_name,
                p.name,
                p.sku,
                p.unit,
                p.reorder_point,
                p.reorder_quantity,
                p.status,
                COALESCE(SUM(ib.on_hand_quantity), 0) AS total_on_hand,
                COALESCE(SUM(ib.reserved_quantity), 0) AS total_reserved,
                COALESCE(SUM(ib.on_hand_quantity - ib.reserved_quantity), 0) AS total_available,
                COUNT(DISTINCT ib.warehouse_id) AS warehouse_count,
                p.created_at,
                p.updated_at
            FROM products p
            LEFT JOIN categories c
                ON c.id = p.category_id
               AND c.workspace_id = p.workspace_id
            LEFT JOIN inventory_balances ib
                ON ib.product_id = p.id
               AND ib.workspace_id = p.workspace_id
            WHERE p.workspace_id = %s
              AND (%s::text IS NULL OR p.status = %s)
              AND (%s::uuid IS NULL OR p.category_id = %s::uuid)
              AND (
                    %s::text IS NULL
                    OR p.name ILIKE %s
                    OR p.sku ILIKE %s
                    OR COALESCE(p.description, '') ILIKE %s
              )
            GROUP BY p.id, c.name
            """
        ) + order_clause + SQL(" LIMIT %s OFFSET %s ")
        params = (
            workspace_id,
            status,
            status,
            category_id,
            category_id,
            search,
            search_pattern,
            search_pattern,
            search_pattern,
            page_size,
            pagination_offset,
        )
        return list(self.connection.execute(base_query, params).fetchall())

    def count_products(
        self,
        *,
        workspace_id: str,
        search: str | None,
        category_id: str | None,
        status: str | None,
    ) -> int:
        search_pattern = f"%{search}%" if search else None
        query = """
            SELECT COUNT(*) AS total
            FROM products p
            WHERE p.workspace_id = %s
              AND (%s::text IS NULL OR p.status = %s)
              AND (%s::uuid IS NULL OR p.category_id = %s::uuid)
              AND (
                    %s::text IS NULL
                    OR p.name ILIKE %s
                    OR p.sku ILIKE %s
                    OR COALESCE(p.description, '') ILIKE %s
              )
        """
        row = self.connection.execute(
            query,
            (
                workspace_id,
                status,
                status,
                category_id,
                category_id,
                search,
                search_pattern,
                search_pattern,
                search_pattern,
            ),
        ).fetchone()
        return int(row["total"])

    def update_product(self, workspace_id: str, product_id: str, fields: dict[str, object]) -> None:
        set_parts, params = build_update_statement(fields=fields, allowed_fields=self.UPDATABLE_FIELDS)
        params.extend([workspace_id, product_id])
        query = SQL("""
            UPDATE products
            SET {},
                updated_at = NOW()
            WHERE workspace_id = %s
              AND id = %s
        """).format(set_parts)
        self.connection.execute(query, params)
