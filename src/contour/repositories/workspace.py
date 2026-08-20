"""Persistence contract for workspace records."""

from __future__ import annotations

from typing import Protocol

from contour.domain.workspace import Workspace, WorkspaceId


class WorkspaceRepository(Protocol):
    """Reads and writes workspace records within an application transaction."""

    def get_workspace(self, workspace_id: WorkspaceId) -> Workspace | None:
        """Return one workspace by stable identity, if it exists."""

    def save_workspace(self, workspace: Workspace) -> None:
        """Persist a new workspace or reject a conflicting identity."""
