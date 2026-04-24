from psycopg import Connection
from psycopg.types.json import Json


class ActivityRepository:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def create_log(
        self,
        *,
        workspace_id: str,
        actor_user_id: str | None,
        action: str,
        entity_type: str,
        entity_id: str | None,
        summary: str,
        metadata: dict | None = None,
    ) -> None:
        query = """
            INSERT INTO activity_logs (
                workspace_id, actor_user_id, action, entity_type, entity_id, summary, metadata
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        self.connection.execute(
            query,
            (workspace_id, actor_user_id, action, entity_type, entity_id, summary, Json(metadata or {})),
        )

    def list_logs(
        self,
        *,
        workspace_id: str,
        page_size: int,
        offset: int,
        actor_user_id: str | None,
        entity_type: str | None,
        action: str | None,
        search: str | None,
    ) -> list[dict]:
        search_pattern = f"%{search}%" if search else None
        query = """
            SELECT
                al.id::text,
                al.workspace_id::text,
                al.actor_user_id::text,
                u.name AS actor_name,
                al.action,
                al.entity_type,
                al.entity_id::text,
                al.summary,
                al.metadata,
                al.created_at
            FROM activity_logs al
            LEFT JOIN users u
              ON u.id = al.actor_user_id
             AND u.workspace_id = al.workspace_id
            WHERE al.workspace_id = %s
              AND (%s::uuid IS NULL OR al.actor_user_id = %s::uuid)
              AND (%s::text IS NULL OR al.entity_type = %s)
              AND (%s::text IS NULL OR al.action = %s)
              AND (
                    %s::text IS NULL
                    OR al.summary ILIKE %s
                    OR al.action ILIKE %s
                    OR al.entity_type ILIKE %s
              )
            ORDER BY al.created_at DESC
            LIMIT %s OFFSET %s
        """
        return list(
            self.connection.execute(
                query,
                (
                    workspace_id,
                    actor_user_id,
                    actor_user_id,
                    entity_type,
                    entity_type,
                    action,
                    action,
                    search,
                    search_pattern,
                    search_pattern,
                    search_pattern,
                    page_size,
                    offset,
                ),
            ).fetchall()
        )

    def count_logs(
        self,
        *,
        workspace_id: str,
        actor_user_id: str | None,
        entity_type: str | None,
        action: str | None,
        search: str | None,
    ) -> int:
        search_pattern = f"%{search}%" if search else None
        query = """
            SELECT COUNT(*) AS total
            FROM activity_logs al
            WHERE al.workspace_id = %s
              AND (%s::uuid IS NULL OR al.actor_user_id = %s::uuid)
              AND (%s::text IS NULL OR al.entity_type = %s)
              AND (%s::text IS NULL OR al.action = %s)
              AND (
                    %s::text IS NULL
                    OR al.summary ILIKE %s
                    OR al.action ILIKE %s
                    OR al.entity_type ILIKE %s
              )
        """
        row = self.connection.execute(
            query,
            (
                workspace_id,
                actor_user_id,
                actor_user_id,
                entity_type,
                entity_type,
                action,
                action,
                search,
                search_pattern,
                search_pattern,
                search_pattern,
            ),
        ).fetchone()
        return int(row["total"])

