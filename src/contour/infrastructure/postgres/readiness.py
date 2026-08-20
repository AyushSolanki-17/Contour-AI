"""PostgreSQL readiness implementation."""

from __future__ import annotations

from sqlalchemy import Engine, literal, select


class PostgresReadinessProbe:
    """Prove PostgreSQL can serve a connection and execute a query."""

    def __init__(self, engine: Engine) -> None:
        """Bind the probe to the process-scoped PostgreSQL engine."""
        self._engine = engine

    def check(self) -> None:
        """Execute a bounded scalar query through the shared connection pool."""
        with self._engine.connect() as connection:
            connection.execute(select(literal(1))).scalar_one()
