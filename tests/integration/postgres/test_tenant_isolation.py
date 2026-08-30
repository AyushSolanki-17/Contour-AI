"""Integration contracts for PostgreSQL-enforced tenant ownership."""

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
    Source,
    SourceId,
    SourceVersion,
    SourceVersionId,
    Tenant,
    TenantId,
    TimePoint,
    Workspace,
    WorkspaceId,
)
from contour.infrastructure.postgres.catalog_transaction import PostgresCatalogTransactionManager
from contour.infrastructure.postgres.engine import create_postgres_engine
from contour.infrastructure.postgres.records_transaction import PostgresRecordTransactionManager
from contour.infrastructure.postgres.tables.catalog import (
    evidence,
    source_versions,
    sources,
    tenants,
    workspaces,
)
from contour.infrastructure.postgres.tables.knowledge import entity_evidence, relationships, runs
from contour.services.catalog_service import CatalogAdmissionService
from contour.settings import DatabaseSettings, Settings

_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def _database_dsn(settings: DatabaseSettings, database: str) -> str:
    """Replace the database component of a validated PostgreSQL DSN."""
    return settings.dsn.rsplit("/", maxsplit=1)[0] + f"/{database}"


def _alembic_config() -> Config:
    """Load repository-local Alembic configuration."""
    return Config(str(_REPOSITORY_ROOT / "alembic.ini"))


def _catalog_record(
    label: str,
) -> tuple[Tenant, Workspace, Source, SourceVersion, EvidenceId, EvidenceLocator]:
    """Return one complete tenant-owned catalog chain for an isolation case."""
    tenant = Tenant(TenantId("TENANT", label), f"Tenant {label}")
    workspace = Workspace(WorkspaceId("WORKSPACE", label), tenant.id, f"Workspace {label}", "owner")
    source = Source(
        SourceId("SOURCE", label),
        tenant.id,
        workspace.id,
        f"https://example.invalid/{label}",
        "fixture",
        "test",
        None,
        "internal",
    )
    digest = ContentDigest(("a" if label == "a" else "b") * 64)
    version = SourceVersion(
        SourceVersionId(source.id, digest),
        tenant.id,
        workspace.id,
        source.id,
        digest,
        TimePoint(datetime(2026, 8, 30, tzinfo=UTC)),
        None,
        TimePoint.unknown(),
        TimePoint.unknown(),
    )
    evidence_id = EvidenceId("EVIDENCE", label)
    locator = EvidenceLocator(tenant.id, workspace.id, version.id, "fixture:body", 0, 1)
    return tenant, workspace, source, version, evidence_id, locator


def _admit_catalogs(
    manager: PostgresCatalogTransactionManager,
) -> tuple[
    tuple[Tenant, Workspace, Source, SourceVersion, EvidenceId, EvidenceLocator],
    tuple[Tenant, Workspace, Source, SourceVersion, EvidenceId, EvidenceLocator],
]:
    """Persist two independent tenant-owned catalog chains."""
    first = _catalog_record("a")
    second = _catalog_record("b")
    service = CatalogAdmissionService(manager)
    for tenant, workspace, source, version, evidence_id, locator in (first, second):
        service.admit(
            tenant=tenant,
            workspace=workspace,
            source=source,
            version=version,
            evidence_id=evidence_id,
            evidence=locator,
        )
    return first, second


def _save_entities_and_job(
    manager: PostgresRecordTransactionManager,
    first: tuple[Tenant, Workspace, Source, SourceVersion, EvidenceId, EvidenceLocator],
    second: tuple[Tenant, Workspace, Source, SourceVersion, EvidenceId, EvidenceLocator],
) -> tuple[Entity, Entity, Job]:
    """Persist records used to test cross-owner foreign-key associations."""
    first_tenant, first_workspace, _, _, first_evidence, _ = first
    second_tenant, second_workspace, _, _, second_evidence, _ = second
    first_entity = Entity(
        EntityId("ENTITY", "a"),
        first_tenant.id,
        first_workspace.id,
        "Entity A",
        (first_evidence,),
        TimePoint.unknown(),
        TimePoint.unknown(),
    )
    second_entity = Entity(
        EntityId("ENTITY", "b"),
        second_tenant.id,
        second_workspace.id,
        "Entity B",
        (second_evidence,),
        TimePoint.unknown(),
        TimePoint.unknown(),
    )
    second_job = Job(
        JobId("JOB", "b"),
        second_tenant.id,
        second_workspace.id,
        "fixture",
        TimePoint.unknown(),
    )
    with manager.transaction() as transaction:
        transaction.entities.save_entity(first_entity)
        transaction.entities.save_entity(second_entity)
        transaction.jobs.save_job(second_job)
    return first_entity, second_entity, second_job


@pytest.mark.integration
def test_tenant_ownership_propagates_through_all_durable_records(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A complete catalog chain stores one unambiguous tenant and workspace tuple."""
    settings = Settings.from_environment()
    database_name = f"contour_tenant_propagation_{uuid.uuid4().hex}"
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
            first, _ = _admit_catalogs(PostgresCatalogTransactionManager(engine))
            tenant, workspace, _, _, _, _ = first
            with engine.connect() as connection:
                assert connection.execute(
                    sa.select(tenants.c.namespace, tenants.c.value).where(
                        tenants.c.namespace == tenant.id.namespace,
                        tenants.c.value == tenant.id.value,
                    )
                ).one() == (tenant.id.namespace, tenant.id.value)
            for table in (workspaces, sources, source_versions, evidence):
                statement = sa.select(table.c.tenant_namespace, table.c.tenant_value).where(
                    table.c.tenant_namespace == tenant.id.namespace,
                    table.c.tenant_value == tenant.id.value,
                )
                with engine.connect() as connection:
                    assert connection.execute(statement).all()
            with engine.connect() as connection:
                assert connection.execute(
                    sa.select(workspaces.c.tenant_namespace, workspaces.c.tenant_value).where(
                        workspaces.c.namespace == workspace.id.namespace,
                        workspaces.c.value == workspace.id.value,
                    )
                ).one() == (tenant.id.namespace, tenant.id.value)
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
def test_database_rejects_cross_owner_relationship_evidence_and_run_links(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Composite foreign keys reject cross-workspace and cross-tenant identifiers."""
    settings = Settings.from_environment()
    database_name = f"contour_tenant_links_{uuid.uuid4().hex}"
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
            first, second = _admit_catalogs(PostgresCatalogTransactionManager(engine))
            first_entity, second_entity, second_job = _save_entities_and_job(
                PostgresRecordTransactionManager(engine), first, second
            )
            first_tenant, first_workspace, _, _, first_evidence, _ = first
            _, _, _, _, second_evidence, _ = second

            invalid_relationship = {
                "namespace": "RELATIONSHIP",
                "value": "cross-workspace",
                "tenant_namespace": first_tenant.id.namespace,
                "tenant_value": first_tenant.id.value,
                "workspace_namespace": first_workspace.id.namespace,
                "workspace_value": first_workspace.id.value,
                "from_namespace": first_entity.id.namespace,
                "from_value": first_entity.id.value,
                "relationship_type": "related_to",
                "to_namespace": second_entity.id.namespace,
                "to_value": second_entity.id.value,
                "primary_evidence_namespace": first_evidence.namespace,
                "primary_evidence_value": first_evidence.value,
            }
            invalid_attachment = {
                "entity_namespace": first_entity.id.namespace,
                "entity_value": first_entity.id.value,
                "tenant_namespace": first_tenant.id.namespace,
                "tenant_value": first_tenant.id.value,
                "workspace_namespace": first_workspace.id.namespace,
                "workspace_value": first_workspace.id.value,
                "position": 1,
                "evidence_namespace": second_evidence.namespace,
                "evidence_value": second_evidence.value,
            }
            invalid_run = {
                "namespace": "RUN",
                "value": "cross-tenant",
                "tenant_namespace": first_tenant.id.namespace,
                "tenant_value": first_tenant.id.value,
                "workspace_namespace": first_workspace.id.namespace,
                "workspace_value": first_workspace.id.value,
                "job_namespace": second_job.id.namespace,
                "job_value": second_job.id.value,
                "status": "pending",
            }
            for table, values in (
                (relationships, invalid_relationship),
                (entity_evidence, invalid_attachment),
                (runs, invalid_run),
            ):
                with pytest.raises(sa.exc.IntegrityError):
                    with engine.begin() as connection:
                        connection.execute(sa.insert(table).values(**values))
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
def test_cross_owner_association_failure_rolls_back_prior_writes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed cross-owner association leaves no earlier write from that transaction."""
    settings = Settings.from_environment()
    database_name = f"contour_tenant_rollback_{uuid.uuid4().hex}"
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
            first, second = _admit_catalogs(PostgresCatalogTransactionManager(engine))
            first_entity, second_entity, _ = _save_entities_and_job(
                PostgresRecordTransactionManager(engine), first, second
            )
            first_tenant, first_workspace, _, _, first_evidence, _ = first
            valid = {
                "namespace": "RELATIONSHIP",
                "value": "rolled-back",
                "tenant_namespace": first_tenant.id.namespace,
                "tenant_value": first_tenant.id.value,
                "workspace_namespace": first_workspace.id.namespace,
                "workspace_value": first_workspace.id.value,
                "from_namespace": first_entity.id.namespace,
                "from_value": first_entity.id.value,
                "relationship_type": "related_to",
                "to_namespace": first_entity.id.namespace,
                "to_value": first_entity.id.value,
                "primary_evidence_namespace": first_evidence.namespace,
                "primary_evidence_value": first_evidence.value,
            }
            invalid = {**valid, "value": "failure", "to_value": second_entity.id.value}
            with pytest.raises(sa.exc.IntegrityError):
                with engine.begin() as connection:
                    connection.execute(sa.insert(relationships).values(**valid))
                    connection.execute(sa.insert(relationships).values(**invalid))
            with engine.connect() as connection:
                assert (
                    connection.execute(
                        sa.select(relationships.c.value).where(
                            relationships.c.namespace == "RELATIONSHIP",
                            relationships.c.value == "rolled-back",
                        )
                    ).one_or_none()
                    is None
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
