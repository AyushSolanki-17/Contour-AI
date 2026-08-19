"""PostgreSQL infrastructure adapters."""

from __future__ import annotations

import psycopg

from contour.config import DatabaseSettings


class PostgresReadinessProbe:
    """Prove PostgreSQL can accept a new connection and answer a query."""

    def __init__(self, database: DatabaseSettings) -> None:
        """Initialize the probe with validated connection settings.

        Args:
            database: PostgreSQL settings used for each readiness check.
        """
        self._database = database

    def check(self) -> None:
        """Open a bounded connection and execute a trivial query.

        Raises:
            psycopg.Error: If PostgreSQL cannot accept or execute the check.
        """
        with psycopg.connect(self._database.dsn, connect_timeout=3) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
