"""Workspace-scoped source registration and listing use cases."""

from __future__ import annotations

from uuid import uuid4

from contour.errors import ResourceNotFoundError
from contour.sources.application.errors import (
    CatalogConflictError,
    SourceAlreadyRegisteredError,
    UnsupportedConnectorError,
)
from contour.sources.application.source_registration_replay import SourceRegistrationReplay
from contour.sources.domain.source import Source, SourceId
from contour.tenancy.application.catalog_store import CatalogTransactionManager
from contour.tenancy.domain.access import AccessContext
from contour.workspaces.domain.workspace import WorkspaceId


class SourceCollectionService:
    """Own source registration and listing in an accessible workspace."""

    def __init__(
        self, transactions: CatalogTransactionManager, supported_connectors: frozenset[str]
    ) -> None:
        """Bind persistence and the explicitly admitted connector capabilities.

        Args:
            transactions: Catalog persistence contract for workspace and source operations.
            supported_connectors: Connector kinds that this deployment accepts.
        """
        self._transactions = transactions
        self._supported_connectors = supported_connectors

    def create_source(
        self,
        *,
        access: AccessContext,
        workspace_id: WorkspaceId,
        connector_kind: str,
        canonical_locator: str,
        scope: str,
        license_name: str | None,
        data_classification: str,
        idempotency_key: str,
    ) -> tuple[Source, bool]:
        """Register or replay one source in an accessible workspace.

        Args:
            access: Verified tenant membership that scopes all reads and writes.
            workspace_id: Nested workspace selected by the client.
            connector_kind: Registered connector capability requested for the source.
            canonical_locator: Stable source-owned locator.
            scope: Source coverage description.
            license_name: Known license or terms label, when available.
            data_classification: Declared handling classification.
            idempotency_key: Client key for safe retry of this registration.

        Returns:
            The accepted source and whether it was recovered from a replay.

        Raises:
            ResourceNotFoundError: If the workspace is absent or inaccessible.
            UnsupportedConnectorError: If the requested connector is not admitted.
            SourceAlreadyRegisteredError: If the source locator is already registered.
            IdempotencyConflictError: If the key was first used for different input.
        """
        if connector_kind not in self._supported_connectors:
            raise UnsupportedConnectorError()
        replay = SourceRegistrationReplay(
            access=access,
            workspace_id=workspace_id,
            key=idempotency_key,
            payload={
                "connector_kind": connector_kind,
                "canonical_locator": canonical_locator,
                "scope": scope,
                "license": license_name,
                "data_classification": data_classification,
            },
        )
        try:
            with self._transactions.transaction() as transaction:
                if transaction.workspaces.get_workspace(access, workspace_id) is None:
                    raise ResourceNotFoundError()
                replayed_source = replay.read(transaction.idempotency)
                if replayed_source is not None:
                    return replayed_source, True
                if transaction.sources.get_source_by_locator(
                    access, workspace_id, connector_kind, canonical_locator
                ):
                    raise SourceAlreadyRegisteredError()
                source = Source(
                    SourceId("SOURCE", str(uuid4())),
                    access.tenant_id,
                    workspace_id,
                    canonical_locator,
                    connector_kind,
                    scope,
                    license_name,
                    data_classification,
                )
                transaction.sources.save_source(access, source)
                replay.save(transaction.idempotency, source)
        except CatalogConflictError:
            replayed = self._replay(replay)
            if replayed is not None:
                return replayed, True
            with self._transactions.transaction() as transaction:
                duplicate = transaction.sources.get_source_by_locator(
                    access, workspace_id, connector_kind, canonical_locator
                )
            if duplicate is not None:
                raise SourceAlreadyRegisteredError() from None
            raise
        return source, False

    def list_sources(self, access: AccessContext, workspace_id: WorkspaceId) -> tuple[Source, ...]:
        """List sources after proving that the nested workspace is accessible.

        Args:
            access: Verified tenant membership that scopes all reads.
            workspace_id: Workspace selected by the client.

        Returns:
            Sources in repository-defined deterministic order.

        Raises:
            ResourceNotFoundError: If the workspace is absent or inaccessible.
        """
        with self._transactions.transaction() as transaction:
            if transaction.workspaces.get_workspace(access, workspace_id) is None:
                raise ResourceNotFoundError()
            return transaction.sources.list_sources(access, workspace_id)

    def _replay(self, replay: SourceRegistrationReplay) -> Source | None:
        """Read a concurrent winner's durable source result.

        Args:
            replay: Source-specific durable replay contract for the request.

        Returns:
            The accepted source when a concurrent request committed, otherwise ``None``.
        """
        with self._transactions.transaction() as transaction:
            return replay.read(transaction.idempotency)
