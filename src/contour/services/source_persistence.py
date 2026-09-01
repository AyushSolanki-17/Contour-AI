"""Application orchestration for durable source content admission."""

from __future__ import annotations

from dataclasses import dataclass

from contour.domain.access import AccessContext
from contour.domain.acquired_content import AcquiredContent
from contour.domain.source import Source
from contour.domain.source_version import SourceVersion, SourceVersionId
from contour.domain.time_point import TimePoint
from contour.repositories.artifact import ArtifactRepository, ArtifactWriteState
from contour.repositories.catalog_transaction import CatalogTransactionManager
from contour.services.catalog_errors import CatalogConflictError
from contour.services.resource_errors import ResourceNotFoundError


@dataclass(frozen=True, slots=True)
class SourcePersistenceResult:
    """The accepted immutable manifest and artifact write outcome."""

    version: SourceVersion
    artifact_state: ArtifactWriteState


class SourcePersistenceService:
    """Persists generic acquired bytes before admitting their immutable manifest."""

    def __init__(
        self,
        artifacts: ArtifactRepository,
        transactions: CatalogTransactionManager,
    ) -> None:
        """Initialize the use case with explicit durable boundaries."""
        self._artifacts = artifacts
        self._transactions = transactions

    def persist(
        self, *, access: AccessContext, acquired: AcquiredContent
    ) -> SourcePersistenceResult:
        """Persist exact bytes and return the first accepted immutable version.

        The artifact is written and integrity-checked before PostgreSQL. A
        database failure can therefore leave only a content-addressed orphan,
        which a retry safely reuses; it cannot admit a manifest after a failed
        artifact operation.

        Raises:
            TypeError: If the input is not source-neutral acquired content.
            ArtifactIntegrityError: If artifact content fails digest verification.
            ArtifactPersistenceError: If artifact persistence cannot finish safely.
            CatalogConflictError: If accepted metadata would be rewritten.
            CatalogPersistenceError: If PostgreSQL persistence fails.
            ResourceNotFoundError: If the logical source is unknown or inaccessible.
        """
        if not isinstance(acquired, AcquiredContent):
            raise TypeError("acquired must be AcquiredContent")

        source = self._source_for(access, acquired)
        artifact_state = self._artifacts.persist(acquired.content, acquired.content_digest)
        version = SourceVersion(
            id=SourceVersionId(acquired.source_id, acquired.content_digest),
            tenant_id=source.tenant_id,
            workspace_id=source.workspace_id,
            source_id=acquired.source_id,
            content_digest=acquired.content_digest,
            observed_at=acquired.observed_at,
            upstream_revision=acquired.upstream_revision,
            source_time=TimePoint.unknown(),
            revision_time=acquired.revision_time,
        )

        try:
            accepted = self._admit_or_get(access, version)
        except CatalogConflictError:
            retry_winner = self._get_retry_winner(access, version)
            if retry_winner is None:
                raise
            accepted = retry_winner
        return SourcePersistenceResult(accepted, artifact_state)

    def _source_for(self, access: AccessContext, acquired: AcquiredContent) -> Source:
        """Return the accepted source needed to bind a version to its owner."""
        with self._transactions.transaction() as transaction:
            source = transaction.sources.get_source(access, acquired.source_id)
        if source is None:
            raise ResourceNotFoundError()
        return source

    def _admit_or_get(self, access: AccessContext, candidate: SourceVersion) -> SourceVersion:
        """Return an equivalent accepted version or insert the candidate."""
        with self._transactions.transaction() as transaction:
            existing = transaction.source_versions.get_source_version(access, candidate.id)
            if existing is not None:
                if _matches_admission(existing, candidate):
                    return existing
                raise CatalogConflictError()
            transaction.source_versions.save_source_version(access, candidate)
        return candidate

    def _get_retry_winner(
        self, access: AccessContext, candidate: SourceVersion
    ) -> SourceVersion | None:
        """Resolve an identical concurrent insert after its transaction commits."""
        with self._transactions.transaction() as transaction:
            existing = transaction.source_versions.get_source_version(access, candidate.id)
        if existing is not None and _matches_admission(existing, candidate):
            return existing
        return None


def _matches_admission(accepted: SourceVersion, candidate: SourceVersion) -> bool:
    """Compare immutable content metadata while retaining the first observation."""
    return (
        accepted.id == candidate.id
        and accepted.source_id == candidate.source_id
        and accepted.content_digest == candidate.content_digest
        and accepted.upstream_revision == candidate.upstream_revision
        and accepted.source_time == candidate.source_time
        and accepted.revision_time == candidate.revision_time
    )
