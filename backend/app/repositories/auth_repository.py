from typing import Any

from psycopg import Connection
from psycopg.types.json import Json


class AuthRepository:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        query = """
            SELECT
                u.id::text,
                u.workspace_id::text,
                u.name,
                u.email,
                u.password_hash,
                u.role,
                u.is_active,
                u.created_at
            FROM users u
            WHERE u.email = %s
            LIMIT 1
        """
        return self.connection.execute(query, (email,)).fetchone()

    def get_user_with_workspace(self, user_id: str, workspace_id: str) -> dict[str, Any] | None:
        query = """
            SELECT
                u.id::text,
                u.workspace_id::text,
                u.name,
                u.email,
                u.role,
                u.is_active,
                u.created_at,
                w.id::text AS workspace_id_check,
                w.name AS workspace_name,
                w.slug AS workspace_slug
            FROM users u
            JOIN workspaces w
                ON w.id = u.workspace_id
            WHERE u.id = %s
              AND u.workspace_id = %s
            LIMIT 1
        """
        return self.connection.execute(query, (user_id, workspace_id)).fetchone()

    def create_workspace(self, *, name: str, slug: str) -> dict[str, Any]:
        query = """
            INSERT INTO workspaces (name, slug)
            VALUES (%s, %s)
            RETURNING id::text, name, slug, created_at, updated_at
        """
        return self.connection.execute(query, (name, slug)).fetchone()

    def create_user(
        self,
        *,
        workspace_id: str,
        name: str,
        email: str,
        password_hash: str,
        role: str,
    ) -> dict[str, Any]:
        query = """
            INSERT INTO users (workspace_id, name, email, password_hash, role)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id::text, workspace_id::text, name, email, role, is_active, created_at
        """
        return self.connection.execute(
            query,
            (workspace_id, name, email, password_hash, role),
        ).fetchone()

    def create_activity_log(
        self,
        *,
        workspace_id: str,
        actor_user_id: str | None,
        action: str,
        entity_type: str,
        entity_id: str | None,
        summary: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        query = """
            INSERT INTO activity_logs (
                workspace_id,
                actor_user_id,
                action,
                entity_type,
                entity_id,
                summary,
                metadata
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
        """
        self.connection.execute(
            query,
            (
                workspace_id,
                actor_user_id,
                action,
                entity_type,
                entity_id,
                summary,
                Json(metadata or {}),
            ),
        )
