"""PostgreSQL infrastructure adapters."""

from __future__ import annotations

import psycopg

from contour.config import DatabaseSettings


class PostgresReadinessProbe:
    """Prove PostgreSQL can accept a new connection and answer a query."""

    def __init__(self, database: DatabaseSettings) -> None:
        self._database = database

    def check(self) -> None:
        with psycopg.connect(self._database.dsn, connect_timeout=3) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
