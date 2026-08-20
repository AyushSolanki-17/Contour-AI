"""Alembic environment using Contour's validated database settings boundary."""

from __future__ import annotations

from alembic import context

from contour.infrastructure.postgres.engine import create_postgres_engine
from contour.infrastructure.postgres.tables.registry import registered_metadata
from contour.settings import Settings

config = context.config
target_metadata = registered_metadata()


def run_migrations_online() -> None:
    """Apply migrations inside one database transaction when the backend supports it."""
    connectable = create_postgres_engine(Settings.from_environment().database)
    try:
        with connectable.connect() as connection:
            context.configure(connection=connection, target_metadata=target_metadata)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        connectable.dispose()


run_migrations_online()
