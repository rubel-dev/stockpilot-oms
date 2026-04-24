from collections.abc import Generator

from psycopg import Connection

from app.db.connection import Database


def get_connection(database: Database) -> Generator[Connection, None, None]:
    with database.connection() as connection:
        yield connection

