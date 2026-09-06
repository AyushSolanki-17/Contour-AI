"""Persistence contract for workspace records."""

from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Protocol

from contour.idempotency import IdempotencyRepository
from contour.tenancy.domain.access import AccessContext
from contour.workspaces.domain.workspace import Workspace, WorkspaceId


class WorkspaceRepository(Protocol):
    """Reads and writes workspace records within an application transaction."""

    def get_workspace(self, access: AccessContext, workspace_id: WorkspaceId) -> Workspace | None:
        """Return one workspace by stable identity, if it exists."""

    def list_workspaces(self, access: AccessContext) -> tuple[Workspace, ...]:
        """Return all workspaces visible in the access context's tenant."""

    def save_workspace(self, access: AccessContext, workspace: Workspace) -> None:
        """Persist a new workspace or reject a conflicting identity."""


@dataclass(frozen=True)
class WorkspaceUnitOfWork:
    """Repositories sharing one transaction for workspaces operations."""

    workspaces: WorkspaceRepository
    idempotency: IdempotencyRepository


class WorkspaceTransactionManager(Protocol):
    """Open an atomic workspaces operation, including its durable replay record."""

    def transaction(self) -> AbstractContextManager[WorkspaceUnitOfWork]:
        """Commit on success and roll back all writes on failure."""
