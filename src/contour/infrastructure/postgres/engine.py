"""PostgreSQL engine construction and connection-pool policy."""

from __future__ import annotations

from sqlalchemy import URL, create_engine
from sqlalchemy.engine import Engine

from contour.settings import DatabaseSettings


def create_postgres_engine(database: DatabaseSettings) -> Engine:
    """Create the process-scoped SQLAlchemy engine for PostgreSQL repositories.

    Args:
        database: Validated settings used to construct a secret-safe URL.

    Returns:
        A pooled engine whose connections are checked before reuse.
    """
    url = URL.create(
        drivername="postgresql+psycopg",
        username=database.username,
        password=database.password,
        host=database.host,
        port=database.port,
        database=database.database,
    )
    return create_engine(
        url,
        connect_args={"connect_timeout": 3},
        hide_parameters=True,
        pool_pre_ping=True,
    )
