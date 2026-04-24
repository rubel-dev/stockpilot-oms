from psycopg import Connection


class InventoryRepository:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def get_product(self, workspace_id: str, product_id: str) -> dict | None:
        query = """
            SELECT id::text, workspace_id::text, name, sku, reorder_point, status
            FROM products
            WHERE workspace_id = %s AND id = %s
            LIMIT 1
        """
        return self.connection.execute(query, (workspace_id, product_id)).fetchone()

    def get_warehouse(self, workspace_id: str, warehouse_id: str) -> dict | None:
        query = """
            SELECT id::text, workspace_id::text, name, code, status
            FROM warehouses
            WHERE workspace_id = %s AND id = %s
            LIMIT 1
        """
        return self.connection.execute(query, (workspace_id, warehouse_id)).fetchone()

    def get_balance_for_update(self, workspace_id: str, product_id: str, warehouse_id: str) -> dict | None:
        query = """
            SELECT
                id::text,
                workspace_id::text,
                product_id::text,
                warehouse_id::text,
                on_hand_quantity,
                reserved_quantity,
                updated_at
            FROM inventory_balances
            WHERE workspace_id = %s
              AND product_id = %s
              AND warehouse_id = %s
            FOR UPDATE
        """
        return self.connection.execute(query, (workspace_id, product_id, warehouse_id)).fetchone()

    def create_balance(self, workspace_id: str, product_id: str, warehouse_id: str) -> dict:
        query = """
            INSERT INTO inventory_balances (workspace_id, product_id, warehouse_id, on_hand_quantity, reserved_quantity)
            VALUES (%s, %s, %s, 0, 0)
            RETURNING id::text, workspace_id::text, product_id::text, warehouse_id::text,
                      on_hand_quantity, reserved_quantity, updated_at
        """
        return self.connection.execute(query, (workspace_id, product_id, warehouse_id)).fetchone()

    def update_balance(
        self,
        *,
        balance_id: str,
        on_hand_quantity: int,
        reserved_quantity: int,
    ) -> None:
        query = """
            UPDATE inventory_balances
            SET on_hand_quantity = %s,
                reserved_quantity = %s,
                updated_at = NOW()
            WHERE id = %s
        """
        self.connection.execute(query, (on_hand_quantity, reserved_quantity, balance_id))

    def insert_movement(
        self,
        *,
        workspace_id: str,
        product_id: str,
        warehouse_id: str,
        destination_warehouse_id: str | None,
        movement_type: str,
        quantity: int,
        quantity_before: int,
        quantity_after: int,
        reason: str | None,
        reference_type: str | None,
        reference_id: str | None,
        notes: str | None,
        created_by: str | None,
    ) -> dict:
        query = """
            INSERT INTO inventory_movements (
                workspace_id, product_id, warehouse_id, destination_warehouse_id, movement_type,
                quantity, quantity_before, quantity_after, reason, reference_type, reference_id,
                notes, created_by
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id::text
        """
        return self.connection.execute(
            query,
            (
                workspace_id,
                product_id,
                warehouse_id,
                destination_warehouse_id,
                movement_type,
                quantity,
                quantity_before,
                quantity_after,
                reason,
                reference_type,
                reference_id,
                notes,
                created_by,
            ),
        ).fetchone()

    def list_balances(
        self,
        *,
        workspace_id: str,
        page_size: int,
        offset: int,
        product_id: str | None,
        warehouse_id: str | None,
        low_stock: bool | None,
        search: str | None,
    ) -> list[dict]:
        search_pattern = f"%{search}%" if search else None
        query = """
            SELECT
                ib.product_id::text,
                p.name AS product_name,
                p.sku AS product_sku,
                ib.warehouse_id::text,
                w.name AS warehouse_name,
                w.code AS warehouse_code,
                p.reorder_point,
                ib.on_hand_quantity,
                ib.reserved_quantity,
                (ib.on_hand_quantity - ib.reserved_quantity) AS available_quantity,
                ib.updated_at
            FROM inventory_balances ib
            JOIN products p
              ON p.id = ib.product_id
             AND p.workspace_id = ib.workspace_id
            JOIN warehouses w
              ON w.id = ib.warehouse_id
             AND w.workspace_id = ib.workspace_id
            WHERE ib.workspace_id = %s
              AND (%s::uuid IS NULL OR ib.product_id = %s::uuid)
              AND (%s::uuid IS NULL OR ib.warehouse_id = %s::uuid)
              AND (
                    %s::boolean IS NULL
                    OR %s = FALSE
                    OR (ib.on_hand_quantity - ib.reserved_quantity) <= p.reorder_point
              )
              AND (
                    %s::text IS NULL
                    OR p.name ILIKE %s
                    OR p.sku ILIKE %s
                    OR w.name ILIKE %s
              )
            ORDER BY ib.updated_at DESC
            LIMIT %s OFFSET %s
        """
        return list(
            self.connection.execute(
                query,
                (
                    workspace_id,
                    product_id,
                    product_id,
                    warehouse_id,
                    warehouse_id,
                    low_stock,
                    low_stock,
                    search,
                    search_pattern,
                    search_pattern,
                    search_pattern,
                    page_size,
                    offset,
                ),
            ).fetchall()
        )

    def count_balances(
        self,
        *,
        workspace_id: str,
        product_id: str | None,
        warehouse_id: str | None,
        low_stock: bool | None,
        search: str | None,
    ) -> int:
        search_pattern = f"%{search}%" if search else None
        query = """
            SELECT COUNT(*) AS total
            FROM inventory_balances ib
            JOIN products p
              ON p.id = ib.product_id
             AND p.workspace_id = ib.workspace_id
            JOIN warehouses w
              ON w.id = ib.warehouse_id
             AND w.workspace_id = ib.workspace_id
            WHERE ib.workspace_id = %s
              AND (%s::uuid IS NULL OR ib.product_id = %s::uuid)
              AND (%s::uuid IS NULL OR ib.warehouse_id = %s::uuid)
              AND (
                    %s::boolean IS NULL
                    OR %s = FALSE
                    OR (ib.on_hand_quantity - ib.reserved_quantity) <= p.reorder_point
              )
              AND (
                    %s::text IS NULL
                    OR p.name ILIKE %s
                    OR p.sku ILIKE %s
                    OR w.name ILIKE %s
              )
        """
        row = self.connection.execute(
            query,
            (
                workspace_id,
                product_id,
                product_id,
                warehouse_id,
                warehouse_id,
                low_stock,
                low_stock,
                search,
                search_pattern,
                search_pattern,
                search_pattern,
            ),
        ).fetchone()
        return int(row["total"])

    def list_movements(
        self,
        *,
        workspace_id: str,
        page_size: int,
        offset: int,
        product_id: str | None,
        warehouse_id: str | None,
        movement_type: str | None,
        search: str | None,
    ) -> list[dict]:
        search_pattern = f"%{search}%" if search else None
        query = """
            SELECT
                im.id::text,
                im.workspace_id::text,
                im.product_id::text,
                p.name AS product_name,
                p.sku AS product_sku,
                im.warehouse_id::text,
                w.name AS warehouse_name,
                im.destination_warehouse_id::text,
                dw.name AS destination_warehouse_name,
                im.movement_type,
                im.quantity,
                im.quantity_before,
                im.quantity_after,
                im.reason,
                im.reference_type,
                im.reference_id::text,
                im.notes,
                im.created_by::text,
                u.name AS created_by_name,
                im.created_at
            FROM inventory_movements im
            JOIN products p
              ON p.id = im.product_id
             AND p.workspace_id = im.workspace_id
            JOIN warehouses w
              ON w.id = im.warehouse_id
             AND w.workspace_id = im.workspace_id
            LEFT JOIN warehouses dw
              ON dw.id = im.destination_warehouse_id
             AND dw.workspace_id = im.workspace_id
            LEFT JOIN users u
              ON u.id = im.created_by
             AND u.workspace_id = im.workspace_id
            WHERE im.workspace_id = %s
              AND (%s::uuid IS NULL OR im.product_id = %s::uuid)
              AND (%s::uuid IS NULL OR im.warehouse_id = %s::uuid)
              AND (%s::text IS NULL OR im.movement_type = %s)
              AND (
                    %s::text IS NULL
                    OR p.name ILIKE %s
                    OR p.sku ILIKE %s
                    OR COALESCE(im.reason, '') ILIKE %s
                    OR COALESCE(im.notes, '') ILIKE %s
              )
            ORDER BY im.created_at DESC
            LIMIT %s OFFSET %s
        """
        return list(
            self.connection.execute(
                query,
                (
                    workspace_id,
                    product_id,
                    product_id,
                    warehouse_id,
                    warehouse_id,
                    movement_type,
                    movement_type,
                    search,
                    search_pattern,
                    search_pattern,
                    search_pattern,
                    search_pattern,
                    page_size,
                    offset,
                ),
            ).fetchall()
        )

    def count_movements(
        self,
        *,
        workspace_id: str,
        product_id: str | None,
        warehouse_id: str | None,
        movement_type: str | None,
        search: str | None,
    ) -> int:
        search_pattern = f"%{search}%" if search else None
        query = """
            SELECT COUNT(*) AS total
            FROM inventory_movements im
            JOIN products p
              ON p.id = im.product_id
             AND p.workspace_id = im.workspace_id
            WHERE im.workspace_id = %s
              AND (%s::uuid IS NULL OR im.product_id = %s::uuid)
              AND (%s::uuid IS NULL OR im.warehouse_id = %s::uuid)
              AND (%s::text IS NULL OR im.movement_type = %s)
              AND (
                    %s::text IS NULL
                    OR p.name ILIKE %s
                    OR p.sku ILIKE %s
                    OR COALESCE(im.reason, '') ILIKE %s
                    OR COALESCE(im.notes, '') ILIKE %s
              )
        """
        row = self.connection.execute(
            query,
            (
                workspace_id,
                product_id,
                product_id,
                warehouse_id,
                warehouse_id,
                movement_type,
                movement_type,
                search,
                search_pattern,
                search_pattern,
                search_pattern,
                search_pattern,
            ),
        ).fetchone()
        return int(row["total"])

