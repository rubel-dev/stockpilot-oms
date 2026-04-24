from typing import Any

from psycopg import Connection


class WorkspaceRepository:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def get_by_id(self, workspace_id: str) -> dict[str, Any] | None:
        query = """
            SELECT id::text, name, slug, created_at, updated_at
            FROM workspaces
            WHERE id = %s
            LIMIT 1
        """
        return self.connection.execute(query, (workspace_id,)).fetchone()

    def update_name(self, workspace_id: str, name: str) -> dict[str, Any]:
        query = """
            UPDATE workspaces
            SET name = %s,
                updated_at = NOW()
            WHERE id = %s
            RETURNING id::text, name, slug, created_at, updated_at
        """
        return self.connection.execute(query, (name, workspace_id)).fetchone()

    def slug_exists(self, slug: str) -> bool:
        query = "SELECT 1 FROM workspaces WHERE slug = %s LIMIT 1"
        return self.connection.execute(query, (slug,)).fetchone() is not None

