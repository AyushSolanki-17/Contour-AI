"""Persistence contract for logical source records."""

from __future__ import annotations

from typing import Protocol

from contour.sources.domain.source import Source, SourceId
from contour.tenancy.domain.access import AccessContext
from contour.workspaces.domain.workspace import WorkspaceId


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
