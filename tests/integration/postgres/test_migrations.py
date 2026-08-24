"""Integration coverage for the clean Contour migration path."""

from __future__ import annotations

import uuid
from pathlib import Path

import psycopg
import pytest
from alembic import command
from alembic.config import Config
from psycopg import sql

from contour.settings import DatabaseSettings, Settings

_REVISION = "20260824_04"
_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def _database_dsn(settings: DatabaseSettings, database: str) -> str:
    """Replace the database component of a validated PostgreSQL DSN."""
    return settings.dsn.rsplit("/", maxsplit=1)[0] + f"/{database}"


def _alembic_config() -> Config:
    """Load repository-local Alembic configuration."""
    return Config(str(_REPOSITORY_ROOT / "alembic.ini"))


@pytest.mark.integration
def test_clean_database_migrates_repeatably(monkeypatch: pytest.MonkeyPatch) -> None:
    """A fresh isolated database reaches and remains at the head revision."""
    try:
        settings = Settings.from_environment()
    except Exception as error:
        pytest.fail(f"Integration configuration is invalid: {error}")

    database_name = f"contour_migration_test_{uuid.uuid4().hex}"
    maintenance_dsn = _database_dsn(settings.database, "postgres")
    test_dsn = _database_dsn(settings.database, database_name)

    # Step 1: Create a unique database so the test never mutates developer data.
    with psycopg.connect(maintenance_dsn, autocommit=True) as maintenance_connection:
        try:
            with maintenance_connection.cursor() as cursor:
                cursor.execute(sql.SQL("CREATE DATABASE {} ").format(sql.Identifier(database_name)))

            # Step 2: Apply the full migration path twice to prove repeatability.
            monkeypatch.setenv("CONTOUR_POSTGRES_DB", database_name)
            command.upgrade(_alembic_config(), "head")
            command.upgrade(_alembic_config(), "head")
            command.check(_alembic_config())

            # Step 3: Verify the revision and durable Phase 0 catalog schema directly.
            with psycopg.connect(test_dsn) as test_connection:
                with test_connection.cursor() as cursor:
                    cursor.execute("SELECT version_num FROM alembic_version")
                    assert cursor.fetchone() == (_REVISION,)
                    cursor.execute(
                        "SELECT tablename FROM pg_tables WHERE schemaname = 'public' "
                        "ORDER BY tablename"
                    )
                    assert cursor.fetchall() == [
                        ("alembic_version",),
                        ("entities",),
                        ("entity_evidence",),
                        ("evidence",),
                        ("jobs",),
                        ("relationship_evidence",),
                        ("relationships",),
                        ("runs",),
                        ("source_versions",),
                        ("sources",),
                        ("workspaces",),
                    ]
        finally:
            # Step 4: Recover safely even when migration or verification fails.
            with maintenance_connection.cursor() as cursor:
                cursor.execute(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                    "WHERE datname = %s AND pid <> pg_backend_pid()",
                    (database_name,),
                )
                cursor.execute(
                    sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(database_name))
                )
