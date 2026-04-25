from __future__ import annotations

from pathlib import Path

import psycopg


def main() -> None:
    sql_dir = Path(__file__).resolve().parents[1] / "sql"
    migration_files = sorted(sql_dir.glob("*.sql"))
    if not migration_files:
        raise RuntimeError("No SQL migration files were found.")

    database_url = _require_database_url()
    with psycopg.connect(database_url, autocommit=True) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                filename TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )

        applied = {
            row[0]
            for row in connection.execute(
                "SELECT filename FROM schema_migrations ORDER BY filename"
            ).fetchall()
        }

        if not applied and _looks_like_existing_database(connection):
            for migration_file in migration_files:
                connection.execute(
                    "INSERT INTO schema_migrations (filename) VALUES (%s) ON CONFLICT (filename) DO NOTHING",
                    (migration_file.name,),
                )
            print("Existing schema detected. Bootstrapped migration history.")
            return

        for migration_file in migration_files:
            if migration_file.name in applied:
                continue

            sql_text = migration_file.read_text(encoding="utf-8").strip()
            if not sql_text:
                connection.execute(
                    "INSERT INTO schema_migrations (filename) VALUES (%s)",
                    (migration_file.name,),
                )
                continue

            connection.execute(sql_text)
            connection.execute(
                "INSERT INTO schema_migrations (filename) VALUES (%s)",
                (migration_file.name,),
            )
            print(f"Applied migration: {migration_file.name}")


def _require_database_url() -> str:
    import os

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required to apply migrations.")
    return database_url


def _looks_like_existing_database(connection: psycopg.Connection) -> bool:
    row = connection.execute(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'workspaces'
        )
        """
    ).fetchone()
    return bool(row and row[0])


if __name__ == "__main__":
    main()
