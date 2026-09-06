"""Persistence contracts for source registration and immutable versions."""

from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Protocol

from contour.idempotency import IdempotencyRepository
from contour.sources.domain.source import Source, SourceId
from contour.sources.domain.source_version import SourceVersion, SourceVersionId
from contour.tenancy.domain.access import AccessContext
from contour.workspaces.domain.workspace import Workspace, WorkspaceId


class SourceRepository(Protocol):
    """Persists logical source records within an application transaction."""

    def get_source(self, access: AccessContext, source_id: SourceId) -> Source | None:
        """Return one logical source by stable identity, if it exists."""

    def list_sources(self, access: AccessContext, workspace_id: WorkspaceId) -> tuple[Source, ...]:
        """Return sources visible in one workspace in stable identity order."""

    def get_source_by_locator(
        self, access: AccessContext, workspace_id: WorkspaceId, connector_kind: str, locator: str
    ) -> Source | None:
        """Return a source by its workspace-local connector and canonical locator."""

    def save_source(self, access: AccessContext, source: Source) -> None:
        """Persist a new source or reject a conflicting identity."""


class SourceVersionRepository(Protocol):
    """Persists immutable content-version records for logical sources."""

    def get_source_version(
        self, access: AccessContext, version_id: SourceVersionId
    ) -> SourceVersion | None:
        """Return one immutable source version by content identity, if it exists."""

    def save_source_version(self, access: AccessContext, version: SourceVersion) -> None:
        """Persist one immutable source version without replacing prior content."""


class WorkspaceLookup(Protocol):
    """Verify a nested workspace without granting workspace mutation access."""

    def get_workspace(self, access: AccessContext, workspace_id: WorkspaceId) -> Workspace | None:
        """Return the selected workspace only within the verified tenant."""


@dataclass(frozen=True)
class SourceUnitOfWork:
    """Repositories sharing one transaction for sources operations."""

    workspaces: WorkspaceLookup
    sources: SourceRepository
    source_versions: SourceVersionRepository
    idempotency: IdempotencyRepository


class SourceTransactionManager(Protocol):
    """Open an atomic sources operation, including its durable replay record."""

    def transaction(self) -> AbstractContextManager[SourceUnitOfWork]:
        """Commit on success and roll back all writes on failure."""
