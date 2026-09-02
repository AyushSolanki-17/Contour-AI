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

from contour.errors import RecordReferenceError
from contour.infrastructure.postgres.catalog_transaction import (
    PostgresCatalogTransactionManager,
)
from contour.infrastructure.postgres.engine import create_postgres_engine
from contour.infrastructure.postgres.records_transaction import PostgresRecordTransactionManager
from contour.infrastructure.postgres.tables.catalog import evidence as evidence_table
from contour.jobs.application.persistence import JobPersistenceService
from contour.jobs.domain.job import Job, JobId
from contour.jobs.domain.run import Run, RunId
from contour.knowledge.application.persistence import KnowledgePersistenceService
from contour.knowledge.domain.entity import Entity, EntityId
from contour.knowledge.domain.evidence import EvidenceId, EvidenceLocator
from contour.knowledge.domain.relationship import Relationship, RelationshipId
from contour.settings import DatabaseSettings, Settings
from contour.sources.application.admission import CatalogAdmissionService
from contour.sources.application.errors import CatalogConflictError, CatalogReferenceError
from contour.sources.domain.source import Source, SourceId
from contour.sources.domain.source_version import ContentDigest, SourceVersion, SourceVersionId
from contour.tenancy.domain.access import AccessContext, Membership, Principal, PrincipalId
from contour.tenancy.domain.tenant import Tenant, TenantId
from contour.time import TimePoint
from contour.workspaces.domain.workspace import Workspace, WorkspaceId

_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def _database_dsn(settings: DatabaseSettings, database: str) -> str:
    """Replace the database component of a validated PostgreSQL DSN."""
    return settings.dsn.rsplit("/", maxsplit=1)[0] + f"/{database}"


def _alembic_config() -> Config:
    """Load repository-local Alembic configuration."""
    return Config(str(_REPOSITORY_ROOT / "alembic.ini"))


def _catalog_records() -> tuple[
    Tenant, Workspace, Source, SourceVersion, EvidenceId, EvidenceLocator
]:
    """Create one catalog admission set with a known and an unknown time."""
    tenant = Tenant(TenantId("TENANT", "test"), "Test tenant")
    workspace = Workspace(WorkspaceId("WORKSPACE", "test"), tenant.id, "Test", "maintainer")
    source = Source(
        SourceId("SOURCE:PEP", "723"),
        tenant.id,
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
        tenant.id,
        workspace.id,
        source.id,
        digest,
        TimePoint(datetime(2026, 8, 20, 13, 0, tzinfo=UTC)),
        "pep-723-2026-08-19",
        TimePoint.unknown(),
        TimePoint(datetime(2026, 8, 19, 10, 30, tzinfo=UTC)),
    )
    evidence_id = EvidenceId("EVIDENCE", "pep-723-replaces")
    evidence = EvidenceLocator(tenant.id, workspace.id, version.id, "header:Replaces", 10, 23)
    return tenant, workspace, source, version, evidence_id, evidence


def _access(tenant: Tenant) -> AccessContext:
    """Return a fixed verified scope for one isolated integration tenant."""
    principal = Principal(PrincipalId("TEST", "catalog-operator"))
    return AccessContext(principal, Membership(principal.id, tenant.id), "catalog-test")


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
            tenant, workspace, source, version, evidence_id, evidence = _catalog_records()
            access = _access(tenant)
            with manager.transaction() as transaction:
                transaction.tenants.save_tenant(tenant)
            CatalogAdmissionService(manager).admit(
                access=access,
                tenant=tenant,
                workspace=workspace,
                source=source,
                version=version,
                evidence_id=evidence_id,
                evidence=evidence,
            )

            with manager.transaction() as transaction:
                assert transaction.workspaces.get_workspace(access, workspace.id) == workspace
                assert transaction.sources.get_source(access, source.id) == source
                assert transaction.source_versions.get_source_version(access, version.id) == version
                assert transaction.evidence.get_evidence(access, evidence_id) == evidence

            with pytest.raises(sa.exc.IntegrityError, match="ck_evidence_valid_span"):
                with engine.begin() as connection:
                    connection.execute(
                        sa.insert(evidence_table).values(
                            namespace="EVIDENCE",
                            value="invalid-half-null-span",
                            tenant_namespace=tenant.id.namespace,
                            tenant_value=tenant.id.value,
                            workspace_namespace=workspace.id.namespace,
                            workspace_value=workspace.id.value,
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
                    transaction.workspaces.save_workspace(access, workspace)

            conflicting_digest = ContentDigest("b" * 64)
            with pytest.raises(CatalogConflictError):
                with manager.transaction() as transaction:
                    transaction.source_versions.save_source_version(
                        access,
                        SourceVersion(
                            SourceVersionId(source.id, conflicting_digest),
                            tenant.id,
                            workspace.id,
                            source.id,
                            conflicting_digest,
                            version.observed_at,
                            version.upstream_revision,
                            version.source_time,
                            version.revision_time,
                        ),
                    )

            with pytest.raises(CatalogReferenceError):
                with manager.transaction() as transaction:
                    transaction.evidence.save_evidence(
                        access,
                        EvidenceId("EVIDENCE", "orphan"),
                        EvidenceLocator(
                            tenant.id,
                            workspace.id,
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
            tenant, workspace, source, _, _, _ = _catalog_records()
            access = _access(tenant)
            with manager.transaction() as transaction:
                transaction.tenants.save_tenant(tenant)

            with pytest.raises(CatalogReferenceError):
                with manager.transaction() as transaction:
                    transaction.workspaces.save_workspace(access, workspace)
                    transaction.sources.save_source(
                        access,
                        Source(
                            source.id,
                            tenant.id,
                            WorkspaceId("WORKSPACE", "missing"),
                            source.canonical_locator,
                            source.source_type,
                            source.scope,
                            source.license,
                            source.data_classification,
                        ),
                    )

            with manager.transaction() as transaction:
                assert transaction.workspaces.get_workspace(access, workspace.id) is None
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
            tenant, workspace, source, version, evidence_id, locator = _catalog_records()
            access = _access(tenant)
            with catalog_manager.transaction() as transaction:
                transaction.tenants.save_tenant(tenant)
            CatalogAdmissionService(catalog_manager).admit(
                access=access,
                tenant=tenant,
                workspace=workspace,
                source=source,
                version=version,
                evidence_id=evidence_id,
                evidence=locator,
            )

            entity_a = Entity(
                EntityId("PEP", "723"),
                tenant.id,
                workspace.id,
                "PEP 723",
                (evidence_id,),
                TimePoint.unknown(),
                TimePoint(datetime(2026, 8, 24, tzinfo=UTC)),
            )
            entity_b = Entity(
                EntityId("PEP", "722"),
                tenant.id,
                workspace.id,
                "PEP 722",
                (evidence_id,),
                TimePoint.unknown(),
                TimePoint.unknown(),
            )
            relationship = Relationship(
                RelationshipId("RELATIONSHIP", "pep-723-replaces-722"),
                tenant.id,
                workspace.id,
                entity_a.id,
                "replaces",
                entity_b.id,
                (evidence_id,),
                TimePoint.unknown(),
                TimePoint.unknown(),
            )
            job = Job(
                JobId("JOB", "ingest-pep-723"),
                tenant.id,
                workspace.id,
                "ingest",
                TimePoint.unknown(),
            )
            failed_run = Run(
                RunId("RUN", "ingest-pep-723-1"),
                tenant.id,
                workspace.id,
                job.id,
                TimePoint.unknown(),
                "failed",
            )
            cancelled_run = Run(
                RunId("RUN", "ingest-pep-723-2"),
                tenant.id,
                workspace.id,
                job.id,
                TimePoint.unknown(),
                "cancelled",
            )
            record_manager = PostgresRecordTransactionManager(engine)
            knowledge_service = KnowledgePersistenceService(record_manager)
            execution_service = JobPersistenceService(record_manager)
            knowledge_service.admit_knowledge(
                access=access, entities=(entity_a, entity_b), relationship=relationship
            )
            execution_service.record(access=access, job=job, runs=(failed_run, cancelled_run))

            with record_manager.transaction() as transaction:
                assert transaction.entities.get_entity(access, entity_a.id) == entity_a
                assert (
                    transaction.relationships.get_relationship(access, relationship.id)
                    == relationship
                )
                assert transaction.jobs.get_job(access, job.id) == job
                assert transaction.runs.get_run(access, failed_run.id) == failed_run
                assert transaction.runs.get_run(access, cancelled_run.id) == cancelled_run

            with pytest.raises(RecordReferenceError):
                with record_manager.transaction() as transaction:
                    transaction.jobs.save_job(
                        access,
                        Job(
                            JobId("JOB", "rolled-back"),
                            tenant.id,
                            workspace.id,
                            "ingest",
                            TimePoint.unknown(),
                        ),
                    )
                    transaction.runs.save_run(
                        access,
                        Run(
                            RunId("RUN", "orphan"),
                            tenant.id,
                            workspace.id,
                            JobId("JOB", "missing"),
                            TimePoint.unknown(),
                        ),
                    )

            with record_manager.transaction() as transaction:
                assert transaction.jobs.get_job(access, JobId("JOB", "rolled-back")) is None

            with pytest.raises(RecordReferenceError):
                with record_manager.transaction() as transaction:
                    transaction.relationships.save_relationship(
                        access,
                        Relationship(
                            RelationshipId("RELATIONSHIP", "invalid-endpoint"),
                            tenant.id,
                            workspace.id,
                            entity_a.id,
                            "replaces",
                            EntityId("PEP", "missing"),
                            (evidence_id,),
                            TimePoint.unknown(),
                            TimePoint.unknown(),
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
