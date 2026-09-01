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

_REVISION = "20260901_09"
_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def _database_dsn(settings: DatabaseSettings, database: str) -> str:
    """Replace the database component of a validated PostgreSQL DSN."""
    return settings.dsn.rsplit("/", maxsplit=1)[0] + f"/{database}"


def _alembic_config() -> Config:
    """Load repository-local Alembic configuration."""
    return Config(str(_REPOSITORY_ROOT / "alembic.ini"))


@pytest.mark.integration
def test_populated_database_migrates_repeatably_to_tenant_ownership(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The prior head upgrades all representative rows into one explicit legacy tenant."""
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

            # Step 2: Seed the prior accepted schema with a version whose
            # observation time was not yet represented.
            monkeypatch.setenv("CONTOUR_POSTGRES_DB", database_name)
            command.upgrade(_alembic_config(), "20260825_05")
            with psycopg.connect(test_dsn) as test_connection:
                with test_connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO workspaces "
                        "(namespace, value, name, owner_name, settings) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        ("WORKSPACE", "migration", "Migration", "maintainer", "{}"),
                    )
                    cursor.execute(
                        "INSERT INTO sources "
                        "(namespace, value, workspace_namespace, workspace_value, "
                        "canonical_locator, source_type, scope, license, data_classification) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (
                            "SOURCE:PEP",
                            "723",
                            "WORKSPACE",
                            "migration",
                            "https://peps.python.org/pep-0723/",
                            "pep",
                            "public",
                            "PSF-2.0",
                            "public",
                        ),
                    )
                    cursor.execute(
                        "INSERT INTO source_versions "
                        "(source_namespace, source_value, content_digest, observation_time_unknown) "
                        "VALUES (%s, %s, %s, %s)",
                        ("SOURCE:PEP", "723", "a" * 64, True),
                    )
                    cursor.execute(
                        "INSERT INTO evidence "
                        "(namespace, value, source_namespace, source_value, content_digest, locator) "
                        "VALUES (%s, %s, %s, %s, %s, %s)",
                        ("EVIDENCE", "migration", "SOURCE:PEP", "723", "a" * 64, "header:Title"),
                    )
                    cursor.execute(
                        "INSERT INTO entities "
                        "(namespace, value, workspace_namespace, workspace_value, label) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        ("ENTITY", "migration-a", "WORKSPACE", "migration", "Migration A"),
                    )
                    cursor.execute(
                        "INSERT INTO entity_evidence "
                        "(entity_namespace, entity_value, position, evidence_namespace, evidence_value) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        ("ENTITY", "migration-a", 0, "EVIDENCE", "migration"),
                    )
                    cursor.execute(
                        "INSERT INTO relationships "
                        "(namespace, value, workspace_namespace, workspace_value, from_namespace, from_value, "
                        "relationship_type, to_namespace, to_value, primary_evidence_namespace, "
                        "primary_evidence_value) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (
                            "RELATIONSHIP",
                            "migration",
                            "WORKSPACE",
                            "migration",
                            "ENTITY",
                            "migration-a",
                            "related_to",
                            "ENTITY",
                            "migration-a",
                            "EVIDENCE",
                            "migration",
                        ),
                    )
                    cursor.execute(
                        "INSERT INTO relationship_evidence "
                        "(relationship_namespace, relationship_value, position, evidence_namespace, evidence_value) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        ("RELATIONSHIP", "migration", 0, "EVIDENCE", "migration"),
                    )
                    cursor.execute(
                        "INSERT INTO jobs "
                        "(namespace, value, workspace_namespace, workspace_value, kind, status) "
                        "VALUES (%s, %s, %s, %s, %s, %s)",
                        ("JOB", "migration", "WORKSPACE", "migration", "ingest", "requested"),
                    )
                    cursor.execute(
                        "INSERT INTO runs (namespace, value, job_namespace, job_value, status) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        ("RUN", "migration", "JOB", "migration", "pending"),
                    )

            # Step 3: Apply the head revision twice to prove repeatability.
            command.upgrade(_alembic_config(), "head")
            command.upgrade(_alembic_config(), "head")
            command.check(_alembic_config())

            # Step 4: Verify the revision, schema, and explicit legacy unknown.
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
                        ("idempotency_records",),
                        ("jobs",),
                        ("memberships",),
                        ("principals",),
                        ("relationship_evidence",),
                        ("relationships",),
                        ("runs",),
                        ("source_versions",),
                        ("sources",),
                        ("tenants",),
                        ("workspaces",),
                    ]
                    cursor.execute(
                        "SELECT observed_at, observation_time_unknown FROM source_versions"
                    )
                    assert cursor.fetchone() == (None, True)
                    cursor.execute("SELECT namespace, value FROM tenants ORDER BY namespace, value")
                    assert cursor.fetchall() == [("LEGACY", "default")]
                    cursor.execute(
                        "SELECT conname FROM pg_constraint "
                        "WHERE conrelid = 'sources'::regclass AND contype = 'u'"
                    )
                    assert "uq_sources_registration" in {row[0] for row in cursor.fetchall()}
                    for table_name in (
                        "workspaces",
                        "sources",
                        "source_versions",
                        "evidence",
                        "entities",
                        "entity_evidence",
                        "relationships",
                        "relationship_evidence",
                        "jobs",
                        "runs",
                    ):
                        cursor.execute(
                            sql.SQL(
                                "SELECT tenant_namespace, tenant_value FROM {} "
                                "ORDER BY tenant_namespace, tenant_value"
                            ).format(sql.Identifier(table_name))
                        )
                        assert cursor.fetchall() == [("LEGACY", "default")]
        finally:
            # Step 5: Recover safely even when migration or verification fails.
            with maintenance_connection.cursor() as cursor:
                cursor.execute(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                    "WHERE datname = %s AND pid <> pg_backend_pid()",
                    (database_name,),
                )
                cursor.execute(
                    sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(database_name))
                )
