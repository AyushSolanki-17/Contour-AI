"""Workspace-scoped source registration and listing use cases."""

from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
from json import dumps
from uuid import uuid4

from contour.domain.access import AccessContext
from contour.domain.source import Source, SourceId
from contour.domain.tenant import TenantId
from contour.domain.workspace import WorkspaceId
from contour.repositories.catalog_transaction import CatalogTransactionManager
from contour.services.catalog_errors import (
    CatalogConflictError,
    IdempotencyConflictError,
    SourceAlreadyRegisteredError,
    UnsupportedConnectorError,
)
from contour.services.resource_errors import ResourceNotFoundError


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
        payload = {
            "connector_kind": connector_kind,
            "canonical_locator": canonical_locator,
            "scope": scope,
            "license": license_name,
            "data_classification": data_classification,
        }
        digest = _payload_digest(payload)
        operation = f"sources:{workspace_id}"
        try:
            with self._transactions.transaction() as transaction:
                if transaction.workspaces.get_workspace(access, workspace_id) is None:
                    raise ResourceNotFoundError()
                replay = transaction.idempotency.get_result(
                    access.principal, str(access.tenant_id), operation, idempotency_key
                )
                if replay is not None:
                    return _source_from_replay(replay, digest), True
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
                transaction.idempotency.save_result(
                    access.principal,
                    str(access.tenant_id),
                    operation,
                    idempotency_key,
                    digest,
                    _source_result(source),
                )
        except CatalogConflictError:
            replayed = self._replay(access, operation, idempotency_key, digest)
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

    def _replay(
        self, access: AccessContext, operation: str, key: str, digest: str
    ) -> Source | None:
        """Read a concurrent winner's durable source result.

        Args:
            access: Verified scope that owns the idempotency namespace.
            operation: Nested operation identifier used for the source route.
            key: Idempotency key that may have concurrently committed.
            digest: Canonical request digest required for replay equivalence.

        Returns:
            The accepted source when a concurrent request committed, otherwise ``None``.
        """
        with self._transactions.transaction() as transaction:
            replay = transaction.idempotency.get_result(
                access.principal, str(access.tenant_id), operation, key
            )
        return None if replay is None else _source_from_replay(replay, digest)


def _payload_digest(payload: Mapping[str, str | None]) -> str:
    """Create a canonical source-request digest for replay comparison.

    Args:
        payload: Source fields that define replay equivalence.

    Returns:
        SHA-256 digest over canonical JSON input.
    """
    return sha256(dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _source_result(source: Source) -> dict[str, str | None]:
    """Serialize durable source fields needed to reconstruct a replay.

    Args:
        source: Newly accepted source.

    Returns:
        JSON-safe result stored beside the idempotency key.
    """
    return {
        "id": str(source.id),
        "tenant_id": str(source.tenant_id),
        "workspace_id": str(source.workspace_id),
        "connector_kind": source.source_type,
        "canonical_locator": source.canonical_locator,
        "scope": source.scope,
        "license": source.license,
        "data_classification": source.data_classification,
    }


def _source_from_replay(replay: tuple[str, dict[str, str | None]], digest: str) -> Source:
    """Validate and reconstruct a source from an idempotency record.

    Args:
        replay: Stored request digest and serialized source result.
        digest: Digest of the request currently being processed.

    Returns:
        Reconstructed source from the durable replay result.

    Raises:
        IdempotencyConflictError: If this key has different accepted input.
    """
    stored_digest, result = replay
    if stored_digest != digest:
        raise IdempotencyConflictError()
    return Source(
        _source_id(str(result["id"])),
        _tenant_id(str(result["tenant_id"])),
        _workspace_id(str(result["workspace_id"])),
        str(result["canonical_locator"]),
        str(result["connector_kind"]),
        str(result["scope"]),
        result["license"],
        str(result["data_classification"]),
    )


def _source_id(value: str) -> SourceId:
    """Rebuild a source identity from trusted internal replay data.

    Args:
        value: Serialized namespaced source identifier.

    Returns:
        Reconstructed source identity.

    Raises:
        ValueError: If durable replay data has an invalid identifier shape.
    """
    namespace, separator, local_value = value.rpartition(":")
    if not separator:
        raise ValueError("invalid stored identifier")
    return SourceId(namespace, local_value)


def _tenant_id(value: str) -> TenantId:
    """Rebuild a tenant identity from trusted internal replay data.

    Args:
        value: Serialized namespaced tenant identifier.

    Returns:
        Reconstructed tenant identity.

    Raises:
        ValueError: If durable replay data has an invalid identifier shape.
    """
    namespace, separator, local_value = value.rpartition(":")
    if not separator:
        raise ValueError("invalid stored identifier")
    return TenantId(namespace, local_value)


def _workspace_id(value: str) -> WorkspaceId:
    """Rebuild a workspace identity from trusted internal replay data.

    Args:
        value: Serialized namespaced workspace identifier.

    Returns:
        Reconstructed workspace identity.

    Raises:
        ValueError: If durable replay data has an invalid identifier shape.
    """
    namespace, separator, local_value = value.rpartition(":")
    if not separator:
        raise ValueError("invalid stored identifier")
    return WorkspaceId(namespace, local_value)
