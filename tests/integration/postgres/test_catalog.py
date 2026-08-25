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
    Entity,
    EntityId,
    EvidenceId,
    EvidenceLocator,
    Job,
    JobId,
    Relationship,
    RelationshipId,
    Run,
    RunId,
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
from contour.infrastructure.postgres.records_transaction import PostgresRecordTransactionManager
from contour.infrastructure.postgres.tables.catalog import evidence as evidence_table
from contour.services.catalog_errors import CatalogConflictError, CatalogReferenceError
from contour.services.catalog_service import CatalogAdmissionService
from contour.services.record_errors import RecordReferenceError
from contour.services.records_service import RecordPersistenceService
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
        TimePoint(datetime(2026, 8, 20, 13, 0, tzinfo=UTC)),
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
                            version.observed_at,
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


@pytest.mark.integration
def test_knowledge_and_execution_records_preserve_evidence_and_attempts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Records round-trip with exact evidence and safely reject missing references."""
    settings = Settings.from_environment()
    database_name = f"contour_records_test_{uuid.uuid4().hex}"
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
            catalog_manager = PostgresCatalogTransactionManager(engine)
            workspace, source, version, evidence_id, locator = _catalog_records()
            CatalogAdmissionService(catalog_manager).admit(
                workspace=workspace,
                source=source,
                version=version,
                evidence_id=evidence_id,
                evidence=locator,
            )

            entity_a = Entity(
                EntityId("PEP", "723"),
                workspace.id,
                "PEP 723",
                (evidence_id,),
                TimePoint.unknown(),
                TimePoint(datetime(2026, 8, 24, tzinfo=UTC)),
            )
            entity_b = Entity(
                EntityId("PEP", "722"),
                workspace.id,
                "PEP 722",
                (evidence_id,),
                TimePoint.unknown(),
                TimePoint.unknown(),
            )
            relationship = Relationship(
                RelationshipId("RELATIONSHIP", "pep-723-replaces-722"),
                workspace.id,
                entity_a.id,
                "replaces",
                entity_b.id,
                (evidence_id,),
                TimePoint.unknown(),
                TimePoint.unknown(),
            )
            job = Job(JobId("JOB", "ingest-pep-723"), workspace.id, "ingest", TimePoint.unknown())
            failed_run = Run(
                RunId("RUN", "ingest-pep-723-1"), job.id, TimePoint.unknown(), "failed"
            )
            cancelled_run = Run(
                RunId("RUN", "ingest-pep-723-2"), job.id, TimePoint.unknown(), "cancelled"
            )
            record_manager = PostgresRecordTransactionManager(engine)
            service = RecordPersistenceService(record_manager)
            service.admit_knowledge(entities=(entity_a, entity_b), relationship=relationship)
            service.record_execution(job=job, runs=(failed_run, cancelled_run))

            with record_manager.transaction() as transaction:
                assert transaction.entities.get_entity(entity_a.id) == entity_a
                assert transaction.relationships.get_relationship(relationship.id) == relationship
                assert transaction.jobs.get_job(job.id) == job
                assert transaction.runs.get_run(failed_run.id) == failed_run
                assert transaction.runs.get_run(cancelled_run.id) == cancelled_run

            with pytest.raises(RecordReferenceError):
                with record_manager.transaction() as transaction:
                    transaction.jobs.save_job(
                        Job(
                            JobId("JOB", "rolled-back"), workspace.id, "ingest", TimePoint.unknown()
                        )
                    )
                    transaction.runs.save_run(
                        Run(RunId("RUN", "orphan"), JobId("JOB", "missing"), TimePoint.unknown())
                    )

            with record_manager.transaction() as transaction:
                assert transaction.jobs.get_job(JobId("JOB", "rolled-back")) is None

            with pytest.raises(RecordReferenceError):
                with record_manager.transaction() as transaction:
                    transaction.relationships.save_relationship(
                        Relationship(
                            RelationshipId("RELATIONSHIP", "invalid-endpoint"),
                            workspace.id,
                            entity_a.id,
                            "replaces",
                            EntityId("PEP", "missing"),
                            (evidence_id,),
                            TimePoint.unknown(),
                            TimePoint.unknown(),
                        )
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
