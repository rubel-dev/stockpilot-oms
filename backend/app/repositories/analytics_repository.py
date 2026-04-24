from psycopg import Connection


class AnalyticsRepository:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def overview(self, workspace_id: str) -> list[dict]:
        query = """
            WITH metrics AS (
                SELECT 'total_products'::text AS key, COUNT(*)::float8 AS value
                FROM products
                WHERE workspace_id = %s
                UNION ALL
                SELECT 'total_units', COALESCE(SUM(on_hand_quantity), 0)::float8
                FROM inventory_balances
                WHERE workspace_id = %s
                UNION ALL
                SELECT 'low_stock_count', COUNT(*)::float8
                FROM inventory_balances ib
                JOIN products p
                  ON p.id = ib.product_id AND p.workspace_id = ib.workspace_id
                WHERE ib.workspace_id = %s
                  AND (ib.on_hand_quantity - ib.reserved_quantity) <= p.reorder_point
                UNION ALL
                SELECT 'open_sales_orders', COUNT(*)::float8
                FROM orders
                WHERE workspace_id = %s AND order_type = 'sales' AND status IN ('confirmed', 'processing')
                UNION ALL
                SELECT 'open_purchase_orders', COUNT(*)::float8
                FROM orders
                WHERE workspace_id = %s AND order_type = 'purchase' AND status IN ('confirmed', 'processing')
                UNION ALL
                SELECT 'pending_alerts', COUNT(*)::float8
                FROM alerts
                WHERE workspace_id = %s AND status = 'open'
            )
            SELECT key, value FROM metrics
        """
        return list(
            self.connection.execute(
                query,
                (workspace_id, workspace_id, workspace_id, workspace_id, workspace_id, workspace_id),
            ).fetchall()
        )

    def stock_by_warehouse(self, workspace_id: str) -> list[dict]:
        query = """
            SELECT
                w.id::text AS warehouse_id,
                w.name AS warehouse_name,
                w.code AS warehouse_code,
                COUNT(DISTINCT ib.product_id) AS sku_count,
                COALESCE(SUM(ib.on_hand_quantity), 0) AS total_on_hand,
                COALESCE(SUM(ib.reserved_quantity), 0) AS total_reserved,
                COALESCE(SUM(ib.on_hand_quantity - ib.reserved_quantity), 0) AS total_available
            FROM warehouses w
            LEFT JOIN inventory_balances ib
              ON ib.workspace_id = w.workspace_id
             AND ib.warehouse_id = w.id
            WHERE w.workspace_id = %s
            GROUP BY w.id
            ORDER BY w.name ASC
        """
        return list(self.connection.execute(query, (workspace_id,)).fetchall())

    def top_moving_products(self, workspace_id: str, limit: int) -> list[dict]:
        query = """
            SELECT
                p.id::text AS product_id,
                p.name AS product_name,
                p.sku AS product_sku,
                SUM(im.quantity) AS total_moved,
                COUNT(*) AS movement_count
            FROM inventory_movements im
            JOIN products p
              ON p.id = im.product_id
             AND p.workspace_id = im.workspace_id
            WHERE im.workspace_id = %s
            GROUP BY p.id
            ORDER BY total_moved DESC, movement_count DESC
            LIMIT %s
        """
        return list(self.connection.execute(query, (workspace_id, limit)).fetchall())

    def monthly_order_trends(self, workspace_id: str) -> list[dict]:
        query = """
            WITH monthly_orders AS (
                SELECT
                    to_char(date_trunc('month', COALESCE(completed_at, created_at)), 'YYYY-MM') AS month_bucket,
                    order_type,
                    COUNT(*) AS order_count,
                    SUM(subtotal_amount)::float8 AS gross_amount
                FROM orders
                WHERE workspace_id = %s
                  AND status IN ('completed', 'shipped', 'processing', 'confirmed')
                GROUP BY 1, 2
            )
            SELECT month_bucket, order_type, order_count, gross_amount
            FROM monthly_orders
            ORDER BY month_bucket ASC, order_type ASC
        """
        return list(self.connection.execute(query, (workspace_id,)).fetchall())

    def supplier_restock_summaries(self, workspace_id: str) -> list[dict]:
        query = """
            SELECT
                s.id::text AS supplier_id,
                s.name AS supplier_name,
                COUNT(DISTINCT o.id) AS purchase_order_count,
                COUNT(DISTINCT oi.product_id) AS unique_products,
                COALESCE(SUM(oi.quantity), 0) AS total_units_ordered,
                COALESCE(SUM(oi.line_total), 0)::float8 AS total_spend
            FROM orders o
            JOIN suppliers s
              ON s.id = o.supplier_id
             AND s.workspace_id = o.workspace_id
            JOIN order_items oi
              ON oi.order_id = o.id
             AND oi.workspace_id = o.workspace_id
            WHERE o.workspace_id = %s
              AND o.order_type = 'purchase'
              AND o.status IN ('confirmed', 'processing', 'completed')
            GROUP BY s.id
            ORDER BY total_spend DESC, total_units_ordered DESC
        """
        return list(self.connection.execute(query, (workspace_id,)).fetchall())

