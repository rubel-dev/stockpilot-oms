from psycopg import Connection
from psycopg.types.json import Json


class AlertRepository:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def find_open_alert(
        self,
        *,
        workspace_id: str,
        alert_type: str,
        product_id: str | None = None,
        warehouse_id: str | None = None,
        order_id: str | None = None,
    ) -> dict | None:
        query = """
            SELECT id::text, status
            FROM alerts
            WHERE workspace_id = %s
              AND alert_type = %s
              AND status = 'open'
              AND ((%s::uuid IS NULL AND product_id IS NULL) OR product_id = %s::uuid)
              AND ((%s::uuid IS NULL AND warehouse_id IS NULL) OR warehouse_id = %s::uuid)
              AND ((%s::uuid IS NULL AND order_id IS NULL) OR order_id = %s::uuid)
            LIMIT 1
        """
        return self.connection.execute(
            query,
            (workspace_id, alert_type, product_id, product_id, warehouse_id, warehouse_id, order_id, order_id),
        ).fetchone()

    def create_alert(
        self,
        *,
        workspace_id: str,
        alert_type: str,
        severity: str,
        product_id: str | None,
        warehouse_id: str | None,
        order_id: str | None,
        title: str,
        message: str,
        metadata: dict | None,
    ) -> dict:
        query = """
            INSERT INTO alerts (
                workspace_id, alert_type, severity, status, product_id, warehouse_id, order_id,
                title, message, metadata
            )
            VALUES (%s, %s, %s, 'open', %s, %s, %s, %s, %s, %s)
            RETURNING id::text
        """
        return self.connection.execute(
            query,
            (
                workspace_id,
                alert_type,
                severity,
                product_id,
                warehouse_id,
                order_id,
                title,
                message,
                Json(metadata or {}),
            ),
        ).fetchone()

    def resolve_alert_by_id(self, workspace_id: str, alert_id: str, resolved_by: str | None) -> dict | None:
        query = """
            UPDATE alerts
            SET status = 'resolved',
                resolved_by = %s,
                resolved_at = NOW(),
                updated_at = NOW()
            WHERE workspace_id = %s
              AND id = %s
            RETURNING id::text, workspace_id::text, alert_type, severity, status,
                      product_id::text, warehouse_id::text, order_id::text,
                      title, message, metadata, resolved_by::text, resolved_at,
                      created_at, updated_at
        """
        return self.connection.execute(query, (resolved_by, workspace_id, alert_id)).fetchone()

    def resolve_open_alert(
        self,
        *,
        workspace_id: str,
        alert_type: str,
        product_id: str | None = None,
        warehouse_id: str | None = None,
        order_id: str | None = None,
        resolved_by: str | None = None,
    ) -> None:
        query = """
            UPDATE alerts
            SET status = 'resolved',
                resolved_by = %s,
                resolved_at = NOW(),
                updated_at = NOW()
            WHERE workspace_id = %s
              AND alert_type = %s
              AND status = 'open'
              AND ((%s::uuid IS NULL AND product_id IS NULL) OR product_id = %s::uuid)
              AND ((%s::uuid IS NULL AND warehouse_id IS NULL) OR warehouse_id = %s::uuid)
              AND ((%s::uuid IS NULL AND order_id IS NULL) OR order_id = %s::uuid)
        """
        self.connection.execute(
            query,
            (
                resolved_by,
                workspace_id,
                alert_type,
                product_id,
                product_id,
                warehouse_id,
                warehouse_id,
                order_id,
                order_id,
            ),
        )

    def dismiss_alert(self, workspace_id: str, alert_id: str, resolved_by: str | None) -> dict | None:
        query = """
            UPDATE alerts
            SET status = 'dismissed',
                resolved_by = %s,
                resolved_at = NOW(),
                updated_at = NOW()
            WHERE workspace_id = %s
              AND id = %s
            RETURNING id::text, workspace_id::text, alert_type, severity, status,
                      product_id::text, warehouse_id::text, order_id::text,
                      title, message, metadata, resolved_by::text, resolved_at,
                      created_at, updated_at
        """
        return self.connection.execute(query, (resolved_by, workspace_id, alert_id)).fetchone()

    def list_alerts(
        self,
        *,
        workspace_id: str,
        page_size: int,
        offset: int,
        alert_type: str | None,
        severity: str | None,
        status: str | None,
        warehouse_id: str | None,
        product_id: str | None,
    ) -> list[dict]:
        query = """
            SELECT id::text, workspace_id::text, alert_type, severity, status,
                   product_id::text, warehouse_id::text, order_id::text, title, message,
                   metadata, resolved_by::text, resolved_at, created_at, updated_at
            FROM alerts
            WHERE workspace_id = %s
              AND (%s::text IS NULL OR alert_type = %s)
              AND (%s::text IS NULL OR severity = %s)
              AND (%s::text IS NULL OR status = %s)
              AND (%s::uuid IS NULL OR warehouse_id = %s::uuid)
              AND (%s::uuid IS NULL OR product_id = %s::uuid)
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        return list(
            self.connection.execute(
                query,
                (
                    workspace_id,
                    alert_type,
                    alert_type,
                    severity,
                    severity,
                    status,
                    status,
                    warehouse_id,
                    warehouse_id,
                    product_id,
                    product_id,
                    page_size,
                    offset,
                ),
            ).fetchall()
        )

    def count_alerts(
        self,
        *,
        workspace_id: str,
        alert_type: str | None,
        severity: str | None,
        status: str | None,
        warehouse_id: str | None,
        product_id: str | None,
    ) -> int:
        query = """
            SELECT COUNT(*) AS total
            FROM alerts
            WHERE workspace_id = %s
              AND (%s::text IS NULL OR alert_type = %s)
              AND (%s::text IS NULL OR severity = %s)
              AND (%s::text IS NULL OR status = %s)
              AND (%s::uuid IS NULL OR warehouse_id = %s::uuid)
              AND (%s::uuid IS NULL OR product_id = %s::uuid)
        """
        row = self.connection.execute(
            query,
            (
                workspace_id,
                alert_type,
                alert_type,
                severity,
                severity,
                status,
                status,
                warehouse_id,
                warehouse_id,
                product_id,
                product_id,
            ),
        ).fetchone()
        return int(row["total"])

    def summary(self, workspace_id: str) -> list[dict]:
        query = """
            SELECT alert_type, severity, status, COUNT(*) AS count
            FROM alerts
            WHERE workspace_id = %s
            GROUP BY alert_type, severity, status
            ORDER BY alert_type, severity, status
        """
        return list(self.connection.execute(query, (workspace_id,)).fetchall())

