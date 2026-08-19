"""Alembic environment using Contour's validated database settings boundary."""

from __future__ import annotations

from alembic import context
from sqlalchemy import create_engine, pool

from contour.config import Settings

config = context.config
target_metadata = None


def _sqlalchemy_url() -> str:
    """Convert the configured DSN to SQLAlchemy's psycopg dialect URL.

    Returns:
        A SQLAlchemy URL for the configured PostgreSQL database.
    """
    database_dsn = Settings.from_environment().database.dsn
    return database_dsn.replace("postgresql://", "postgresql+psycopg://", 1)


def run_migrations_online() -> None:
    """Apply migrations inside one database transaction when the backend supports it."""
    connectable = create_engine(_sqlalchemy_url(), poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
