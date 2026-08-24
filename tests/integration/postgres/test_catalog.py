"""Integration contracts for durable catalog and evidence persistence."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path

import psycopg
import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from psycopg import sql

from contour.domain import (
    ContentDigest,
    EvidenceId,
    EvidenceLocator,
    Source,
    SourceId,
    SourceVersion,
    SourceVersionId,
    TimePoint,
    Workspace,
    WorkspaceId,
)
from contour.infrastructure.postgres.catalog_transaction import (
    PostgresCatalogTransactionManager,
)
from contour.infrastructure.postgres.engine import create_postgres_engine
from contour.infrastructure.postgres.tables.catalog import evidence as evidence_table
from contour.services.catalog_errors import CatalogConflictError, CatalogReferenceError
from contour.services.catalog_service import CatalogAdmissionService
from contour.settings import DatabaseSettings, Settings

_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def _database_dsn(settings: DatabaseSettings, database: str) -> str:
    """Replace the database component of a validated PostgreSQL DSN."""
    return settings.dsn.rsplit("/", maxsplit=1)[0] + f"/{database}"


def _alembic_config() -> Config:
    """Load repository-local Alembic configuration."""
    return Config(str(_REPOSITORY_ROOT / "alembic.ini"))


def _catalog_records() -> tuple[Workspace, Source, SourceVersion, EvidenceId, EvidenceLocator]:
    """Create one catalog admission set with a known and an unknown time."""
    workspace = Workspace(WorkspaceId("WORKSPACE", "test"), "Test", "maintainer")
    source = Source(
        SourceId("SOURCE:PEP", "723"),
        workspace.id,
        "https://peps.python.org/pep-0723/",
        "pep",
        "public",
        "PSF-2.0",
        "public",
    )
    digest = ContentDigest("a" * 64)
    version = SourceVersion(
        SourceVersionId(source.id, digest),
        source.id,
        digest,
        "pep-723-2026-08-19",
        TimePoint.unknown(),
        TimePoint(datetime(2026, 8, 19, 10, 30, tzinfo=UTC)),
    )
    evidence_id = EvidenceId("EVIDENCE", "pep-723-replaces")
    evidence = EvidenceLocator(version.id, "header:Replaces", 10, 23)
    return workspace, source, version, evidence_id, evidence


@pytest.mark.integration
def test_catalog_records_round_trip_and_reject_invalid_references(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Catalog persistence retains exact values and rejects duplicate or orphan writes."""
    settings = Settings.from_environment()
    database_name = f"contour_catalog_test_{uuid.uuid4().hex}"
    maintenance_dsn = _database_dsn(settings.database, "postgres")
    engine = None

    with psycopg.connect(maintenance_dsn, autocommit=True) as maintenance_connection:
        try:
            with maintenance_connection.cursor() as cursor:
                cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name)))
            monkeypatch.setenv("CONTOUR_POSTGRES_DB", database_name)
            command.upgrade(_alembic_config(), "head")
            engine = create_postgres_engine(
                DatabaseSettings(
                    database_name,
                    settings.database.username,
                    settings.database.password,
                    settings.database.host,
                    settings.database.port,
                )
            )
            manager = PostgresCatalogTransactionManager(engine)
            workspace, source, version, evidence_id, evidence = _catalog_records()
            CatalogAdmissionService(manager).admit(
                workspace=workspace,
                source=source,
                version=version,
                evidence_id=evidence_id,
                evidence=evidence,
            )

            with manager.transaction() as transaction:
                assert transaction.workspaces.get_workspace(workspace.id) == workspace
                assert transaction.sources.get_source(source.id) == source
                assert transaction.source_versions.get_source_version(version.id) == version
                assert transaction.evidence.get_evidence(evidence_id) == evidence

            with pytest.raises(sa.exc.IntegrityError, match="ck_evidence_valid_span"):
                with engine.begin() as connection:
                    connection.execute(
                        sa.insert(evidence_table).values(
                            namespace="EVIDENCE",
                            value="invalid-half-null-span",
                            source_namespace=version.source_id.namespace,
                            source_value=version.source_id.value,
                            content_digest=version.content_digest.value,
                            locator="header:Replaces",
                            start_offset=None,
                            end_offset=1,
                        )
                    )

            with pytest.raises(CatalogConflictError):
                with manager.transaction() as transaction:
                    transaction.workspaces.save_workspace(workspace)

            conflicting_digest = ContentDigest("b" * 64)
            with pytest.raises(CatalogConflictError):
                with manager.transaction() as transaction:
                    transaction.source_versions.save_source_version(
                        SourceVersion(
                            SourceVersionId(source.id, conflicting_digest),
                            source.id,
                            conflicting_digest,
                            version.upstream_revision,
                            version.source_time,
                            version.revision_time,
                        )
                    )

            with pytest.raises(CatalogReferenceError):
                with manager.transaction() as transaction:
                    transaction.evidence.save_evidence(
                        EvidenceId("EVIDENCE", "orphan"),
                        EvidenceLocator(
                            SourceVersionId(source.id, ContentDigest("b" * 64)),
                            "header:Replaces",
                        ),
                    )
        finally:
            if engine is not None:
                engine.dispose()
            with maintenance_connection.cursor() as cursor:
                cursor.execute(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                    "WHERE datname = %s AND pid <> pg_backend_pid()",
                    (database_name,),
                )
                cursor.execute(
                    sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(database_name))
                )


@pytest.mark.integration
def test_failed_catalog_transaction_rolls_back_all_prior_writes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A database error after a write leaves no partially admitted workspace."""
    settings = Settings.from_environment()
    database_name = f"contour_catalog_rollback_test_{uuid.uuid4().hex}"
    maintenance_dsn = _database_dsn(settings.database, "postgres")
    engine = None

    with psycopg.connect(maintenance_dsn, autocommit=True) as maintenance_connection:
        try:
            with maintenance_connection.cursor() as cursor:
                cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name)))
            monkeypatch.setenv("CONTOUR_POSTGRES_DB", database_name)
            command.upgrade(_alembic_config(), "head")
            engine = create_postgres_engine(
                DatabaseSettings(
                    database_name,
                    settings.database.username,
                    settings.database.password,
                    settings.database.host,
                    settings.database.port,
                )
            )
            manager = PostgresCatalogTransactionManager(engine)
            workspace, source, _, _, _ = _catalog_records()

            with pytest.raises(CatalogReferenceError):
                with manager.transaction() as transaction:
                    transaction.workspaces.save_workspace(workspace)
                    transaction.sources.save_source(
                        Source(
                            source.id,
                            WorkspaceId("WORKSPACE", "missing"),
                            source.canonical_locator,
                            source.source_type,
                            source.scope,
                            source.license,
                            source.data_classification,
                        )
                    )

            with manager.transaction() as transaction:
                assert transaction.workspaces.get_workspace(workspace.id) is None
        finally:
            if engine is not None:
                engine.dispose()
            with maintenance_connection.cursor() as cursor:
                cursor.execute(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                    "WHERE datname = %s AND pid <> pg_backend_pid()",
                    (database_name,),
                )
                cursor.execute(
                    sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(database_name))
                )
