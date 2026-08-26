"""Integrated PEP artifact and immutable-manifest persistence contracts."""

from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

import psycopg
import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from psycopg import sql

from contour.domain import (
    AcquiredContent,
    ContentDigest,
    Source,
    SourceId,
    SourceVersionId,
    TimePoint,
    Workspace,
    WorkspaceId,
)
from contour.infrastructure.artifact.filesystem import FileSystemArtifactRepository
from contour.infrastructure.postgres.catalog_transaction import (
    PostgresCatalogTransactionManager,
)
from contour.infrastructure.postgres.engine import create_postgres_engine
from contour.infrastructure.postgres.tables.catalog import source_versions
from contour.infrastructure.source.pep import PepAcquisitionService, PepPreflightService
from contour.infrastructure.source.pep_fixture import PepFixtureSourceAdapter, PinnedPepFixture
from contour.repositories.artifact import ArtifactWriteState
from contour.services.artifact_errors import (
    ArtifactIntegrityError,
    ArtifactNotFoundError,
    ArtifactPersistenceError,
)
from contour.services.catalog_errors import CatalogConflictError, CatalogReferenceError
from contour.services.source_persistence import SourcePersistenceService
from contour.settings import DatabaseSettings, Settings

_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_FIXTURE_PATH = _REPOSITORY_ROOT / "tests" / "fixtures" / "pep_0723.html"


def _database_dsn(settings: DatabaseSettings, database: str) -> str:
    """Replace the database component of a validated PostgreSQL DSN."""
    return settings.dsn.rsplit("/", maxsplit=1)[0] + f"/{database}"


def _alembic_config() -> Config:
    """Load repository-local Alembic configuration."""
    return Config(str(_REPOSITORY_ROOT / "alembic.ini"))


def _source(workspace_id: WorkspaceId, pep_number: int) -> Source:
    """Create one supported public PEP source."""
    return Source(
        SourceId("SOURCE:PEP", str(pep_number)),
        workspace_id,
        f"https://peps.python.org/pep-{pep_number:04d}/",
        "pep",
        "public",
        "PSF-2.0",
        "public",
    )


def _acquire(
    source: Source,
    content: bytes,
    *,
    upstream_revision: str | None,
    revision_time: TimePoint,
) -> AcquiredContent:
    """Admit deterministic bytes through the accepted PEP acquisition boundary."""
    digest = ContentDigest(sha256(content).hexdigest())
    fixture = PinnedPepFixture(
        int(source.id.value),
        content,
        digest,
        upstream_revision,
        revision_time,
    )
    service = PepAcquisitionService(PepPreflightService(), PepFixtureSourceAdapter((fixture,)))
    return service.acquire(source, observed_at=TimePoint(datetime(2026, 8, 25, 8, 0, tzinfo=UTC)))


@pytest.mark.integration
def test_pep_bytes_and_manifest_are_idempotent_immutable_and_recoverable(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Real artifact and PostgreSQL failures never admit an invalid manifest."""
    settings = Settings.from_environment()
    database_name = f"contour_pep_persistence_test_{uuid.uuid4().hex}"
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
            workspace = Workspace(WorkspaceId("WORKSPACE", "pep-ingestion"), "PEPs", "maintainer")
            pep_723 = _source(workspace.id, 723)
            with manager.transaction() as transaction:
                transaction.workspaces.save_workspace(workspace)
                transaction.sources.save_source(pep_723)

            artifact_repository = FileSystemArtifactRepository(tmp_path / "artifacts")
            service = SourcePersistenceService(artifact_repository, manager)
            fixture_content = _FIXTURE_PATH.read_bytes()
            acquisition = _acquire(
                pep_723,
                fixture_content,
                upstream_revision="pep-723-fixture-r1",
                revision_time=TimePoint(datetime(2026, 8, 24, tzinfo=UTC)),
            )
            first_observation = TimePoint(datetime(2026, 8, 25, 8, 0, tzinfo=UTC))
            later_observation = TimePoint(datetime(2026, 8, 25, 9, 0, tzinfo=UTC))

            first = service.persist(acquisition)
            repeated = service.persist(replace(acquisition, observed_at=later_observation))

            assert first.artifact_state is ArtifactWriteState.CREATED
            assert repeated.artifact_state is ArtifactWriteState.UNCHANGED
            assert repeated.version == first.version
            assert first.version.observed_at == first_observation
            assert first.version.source_id == pep_723.id
            assert first.version.content_digest == acquisition.content_digest
            assert artifact_repository.retrieve(acquisition.content_digest) == fixture_content
            with manager.transaction() as transaction:
                assert (
                    transaction.source_versions.get_source_version(first.version.id)
                    == first.version
                )
            with engine.connect() as connection:
                assert (
                    connection.scalar(sa.select(sa.func.count()).select_from(source_versions)) == 1
                )

            with pytest.raises(CatalogConflictError):
                service.persist(
                    replace(acquisition, upstream_revision="conflicting-revision"),
                )

            changed_content = b"<html><body><h1>PEP 723 changed</h1></body></html>"
            changed_acquisition = _acquire(
                pep_723,
                changed_content,
                upstream_revision=acquisition.upstream_revision,
                revision_time=acquisition.revision_time,
            )
            with pytest.raises(CatalogConflictError):
                service.persist(changed_acquisition)
            with manager.transaction() as transaction:
                assert (
                    transaction.source_versions.get_source_version(
                        SourceVersionId(pep_723.id, changed_acquisition.content_digest)
                    )
                    is None
                )

            artifact_path = artifact_repository.artifact_path(acquisition.content_digest)
            artifact_path.unlink()
            with pytest.raises(ArtifactNotFoundError):
                artifact_repository.retrieve(acquisition.content_digest)
            assert service.persist(acquisition).artifact_state is ArtifactWriteState.CREATED

            artifact_path.write_bytes(b"corrupt artifact")
            with pytest.raises(ArtifactIntegrityError):
                artifact_repository.retrieve(acquisition.content_digest)
            assert service.persist(acquisition).artifact_state is ArtifactWriteState.REPAIRED
            assert artifact_repository.retrieve(acquisition.content_digest) == fixture_content

            pep_724 = _source(workspace.id, 724)
            acquisition_724 = _acquire(
                pep_724,
                b"<html><body><h1>PEP 724</h1></body></html>",
                upstream_revision="pep-724-fixture-r1",
                revision_time=TimePoint(datetime(2026, 8, 24, 1, 0, tzinfo=UTC)),
            )
            with pytest.raises(CatalogReferenceError):
                service.persist(acquisition_724)
            assert (
                artifact_repository.retrieve(acquisition_724.content_digest)
                == acquisition_724.content
            )

            with manager.transaction() as transaction:
                assert (
                    transaction.source_versions.get_source_version(
                        SourceVersionId(pep_724.id, acquisition_724.content_digest)
                    )
                    is None
                )
                transaction.sources.save_source(pep_724)
            recovered_724 = service.persist(acquisition_724)
            assert recovered_724.artifact_state is ArtifactWriteState.UNCHANGED

            pep_725 = _source(workspace.id, 725)
            with manager.transaction() as transaction:
                transaction.sources.save_source(pep_725)
            acquisition_725 = _acquire(
                pep_725,
                b"<html><body><h1>PEP 725</h1></body></html>",
                upstream_revision=None,
                revision_time=TimePoint.unknown(),
            )
            blocked_root = tmp_path / "blocked-artifact-root"
            blocked_root.write_text("not a directory", encoding="utf-8")
            blocked_service = SourcePersistenceService(
                FileSystemArtifactRepository(blocked_root), manager
            )
            with pytest.raises(ArtifactPersistenceError):
                blocked_service.persist(acquisition_725)
            with manager.transaction() as transaction:
                assert (
                    transaction.source_versions.get_source_version(
                        SourceVersionId(pep_725.id, acquisition_725.content_digest)
                    )
                    is None
                )

            recovered_725 = service.persist(acquisition_725)
            assert recovered_725.version.upstream_revision is None
            assert not recovered_725.version.revision_time.is_known
            with engine.connect() as connection:
                assert (
                    connection.scalar(sa.select(sa.func.count()).select_from(source_versions)) == 3
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
