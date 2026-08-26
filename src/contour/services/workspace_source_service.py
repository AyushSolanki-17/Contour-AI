"""Source-neutral workspace and logical-source application operations."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from contour.domain.source import Source, SourceId
from contour.domain.workspace import Workspace, WorkspaceId
from contour.repositories.catalog_transaction import CatalogTransactionManager
from contour.services.catalog_errors import (
    CatalogConflictError,
    CatalogPersistenceError,
    CatalogReferenceError,
)
from contour.services.health_service import DependencyUnavailableError
from contour.services.workspace_source_errors import (
    ResourceConflictError,
    ResourceNotFoundError,
    UnsupportedSourceError,
)


class SourceRegistrationPolicy(Protocol):
    """Reports whether a configured adapter accepts one source definition."""

    def supports(self, source: Source) -> bool:
        """Return whether the source can be handled by a configured capability."""


class WorkspaceSourceService:
    """Creates and inspects workspaces and their registered logical sources."""

    def __init__(
        self,
        transactions: CatalogTransactionManager,
        source_policies: tuple[SourceRegistrationPolicy, ...],
        *,
        local_owner: str,
    ) -> None:
        """Initialize product operations with persistence and configured capabilities."""
        self._transactions = transactions
        self._source_policies = source_policies
        self._local_owner = local_owner

    def put_workspace(self, workspace_id: WorkspaceId, *, name: str) -> Workspace:
        """Create a workspace or return its exactly matching accepted representation.

        Raises:
            ResourceConflictError: If the identity already has a different representation.
            DependencyUnavailableError: If durable catalog storage is unavailable.
        """
        candidate = Workspace(workspace_id, name, self._local_owner)

        def operation() -> Workspace:
            with self._transactions.transaction() as transaction:
                accepted = transaction.workspaces.get_workspace(workspace_id)
                if accepted is None:
                    transaction.workspaces.save_workspace(candidate)
                    return candidate
                return _require_exact_replay(accepted, candidate)

        return self._run_idempotent(
            operation,
            candidate=candidate,
            replay=lambda: self.get_workspace(workspace_id),
        )

    def get_workspace(self, workspace_id: WorkspaceId) -> Workspace:
        """Return an accepted workspace by identity.

        Raises:
            ResourceNotFoundError: If no workspace has the supplied identity.
            DependencyUnavailableError: If durable catalog storage is unavailable.
        """
        try:
            with self._transactions.transaction() as transaction:
                workspace = transaction.workspaces.get_workspace(workspace_id)
        except CatalogPersistenceError as error:
            raise DependencyUnavailableError() from error
        if workspace is None:
            raise ResourceNotFoundError()
        return workspace

    def put_source(self, source: Source) -> Source:
        """Register a supported source or return an exact accepted replay.

        Raises:
            UnsupportedSourceError: If no configured source capability accepts the source.
            ResourceNotFoundError: If the owning workspace does not exist.
            ResourceConflictError: If the identity already has a different representation.
            DependencyUnavailableError: If durable catalog storage is unavailable.
        """
        if not any(policy.supports(source) for policy in self._source_policies):
            raise UnsupportedSourceError()

        def operation() -> Source:
            with self._transactions.transaction() as transaction:
                if transaction.workspaces.get_workspace(source.workspace_id) is None:
                    raise ResourceNotFoundError()
                accepted = transaction.sources.get_source(source.id)
                if accepted is None:
                    transaction.sources.save_source(source)
                    return source
                return _require_exact_replay(accepted, source)

        return self._run_idempotent(
            operation,
            candidate=source,
            replay=lambda: self.get_source(source.workspace_id, source.id),
        )

    def get_source(self, workspace_id: WorkspaceId, source_id: SourceId) -> Source:
        """Return a source only through the workspace that owns it.

        Raises:
            ResourceNotFoundError: If the workspace-scoped source is unavailable.
            DependencyUnavailableError: If durable catalog storage is unavailable.
        """
        try:
            with self._transactions.transaction() as transaction:
                source = transaction.sources.get_source(source_id)
        except CatalogPersistenceError as error:
            raise DependencyUnavailableError() from error
        if source is None or source.workspace_id != workspace_id:
            raise ResourceNotFoundError()
        return source

    def _run_idempotent[ResourceT: (Workspace, Source)](
        self,
        operation: Callable[[], ResourceT],
        *,
        candidate: ResourceT,
        replay: Callable[[], ResourceT],
    ) -> ResourceT:
        """Run a create operation and resolve a concurrent exact replay safely."""
        try:
            return operation()
        except CatalogConflictError:
            try:
                return _require_exact_replay(replay(), candidate)
            except ResourceNotFoundError as error:
                raise ResourceConflictError() from error
        except CatalogReferenceError as error:
            raise ResourceNotFoundError() from error
        except CatalogPersistenceError as error:
            raise DependencyUnavailableError() from error


def _require_exact_replay[ResourceT: (Workspace, Source)](
    accepted: ResourceT,
    candidate: ResourceT,
) -> ResourceT:
    """Return an exact accepted representation or reject identity reuse."""
    if accepted != candidate:
        raise ResourceConflictError()
    return accepted
