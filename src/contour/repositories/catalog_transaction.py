"""Transaction contracts for atomic catalog operations."""

from __future__ import annotations

from types import TracebackType
from typing import Protocol, Self

from contour.repositories.access import MembershipRepository, PrincipalRepository
from contour.repositories.evidence import EvidenceRepository
from contour.repositories.source import SourceRepository
from contour.repositories.source_version import SourceVersionRepository
from contour.repositories.tenant import TenantRepository
from contour.repositories.workspace import WorkspaceRepository


class CatalogUnitOfWork(Protocol):
    """Provides repositories for one atomic catalog admission operation."""

    @property
    def tenants(self) -> TenantRepository:
        """Return the tenant repository bound to this transaction."""

    @property
    def principals(self) -> PrincipalRepository:
        """Return the principal repository bound to this transaction."""

    @property
    def memberships(self) -> MembershipRepository:
        """Return the membership repository bound to this transaction."""

    @property
    def workspaces(self) -> WorkspaceRepository:
        """Return the workspace repository bound to this transaction."""

    @property
    def sources(self) -> SourceRepository:
        """Return the source repository bound to this transaction."""

    @property
    def source_versions(self) -> SourceVersionRepository:
        """Return the immutable source-version repository bound to this transaction."""

    @property
    def evidence(self) -> EvidenceRepository:
        """Return the exact evidence repository bound to this transaction."""

    def __enter__(self) -> Self:
        """Begin the catalog transaction and return its repositories."""

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Commit on success or discard all catalog writes on failure."""


class CatalogTransactionManager(Protocol):
    """Creates one explicit atomic boundary for catalog admission."""

    def transaction(self) -> CatalogUnitOfWork:
        """Return a fresh catalog transaction."""
