"""Tenant-scoped workspace collection use cases and replay handling."""

from __future__ import annotations

from hashlib import sha256
from json import dumps
from uuid import uuid4

from contour.sources.application.errors import CatalogConflictError, IdempotencyConflictError
from contour.tenancy.application.catalog_store import CatalogTransactionManager
from contour.tenancy.domain.access import AccessContext
from contour.tenancy.domain.tenant import TenantId
from contour.workspaces.domain.workspace import Workspace, WorkspaceId


class WorkspaceCollectionService:
    """Own workspace creation and listing within a previously verified tenant."""

    def __init__(self, transactions: CatalogTransactionManager) -> None:
        """Bind the catalog transaction boundary used for workspace writes.

        Args:
            transactions: Persistence contract providing workspace and idempotency stores.
        """
        self._transactions = transactions

    def create_workspace(
        self, access: AccessContext, name: str, key: str
    ) -> tuple[Workspace, bool]:
        """Create or replay one tenant-scoped workspace request.

        Args:
            access: Verified tenant membership selected by the caller.
            name: Validated workspace display name.
            key: Client idempotency key for this workspace request.

        Returns:
            The accepted workspace and whether it was recovered from a replay.

        Raises:
            IdempotencyConflictError: If the key was first used for different input.
        """
        digest = _payload_digest(name)
        try:
            with self._transactions.transaction() as transaction:
                replay = transaction.idempotency.get_result(
                    access.principal, str(access.tenant_id), "workspaces", key
                )
                if replay is not None:
                    return _workspace_from_replay(replay, digest), True
                workspace = Workspace(
                    WorkspaceId("WORKSPACE", str(uuid4())),
                    access.tenant_id,
                    name,
                    str(access.principal.id),
                )
                transaction.workspaces.save_workspace(access, workspace)
                transaction.idempotency.save_result(
                    access.principal,
                    str(access.tenant_id),
                    "workspaces",
                    key,
                    digest,
                    _workspace_result(workspace),
                )
        except CatalogConflictError:
            replayed = self._replay(access, key, digest)
            if replayed is None:
                raise
            return replayed, True
        return workspace, False

    def list_workspaces(self, access: AccessContext) -> tuple[Workspace, ...]:
        """List workspaces only in the tenant represented by verified access.

        Args:
            access: Verified tenant membership that scopes the query.

        Returns:
            Workspace values in repository-defined deterministic order.
        """
        with self._transactions.transaction() as transaction:
            return transaction.workspaces.list_workspaces(access)

    def _replay(self, access: AccessContext, key: str, digest: str) -> Workspace | None:
        """Read a concurrent winner's durable workspace result.

        Args:
            access: Verified scope that owns the idempotency namespace.
            key: Idempotency key that may have concurrently committed.
            digest: Canonical request digest required for replay equivalence.

        Returns:
            The accepted workspace when a concurrent request committed, otherwise ``None``.
        """
        with self._transactions.transaction() as transaction:
            replay = transaction.idempotency.get_result(
                access.principal, str(access.tenant_id), "workspaces", key
            )
        return None if replay is None else _workspace_from_replay(replay, digest)


def _payload_digest(name: str) -> str:
    """Create the stable workspace-request digest used for replay comparison.

    Args:
        name: Validated workspace name supplied by the client.

    Returns:
        SHA-256 digest over canonical JSON input.
    """
    return sha256(dumps({"name": name}, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _workspace_result(workspace: Workspace) -> dict[str, str | None]:
    """Serialize durable workspace fields needed to reconstruct a replay.

    Args:
        workspace: Newly accepted workspace.

    Returns:
        JSON-safe result stored beside the idempotency key.
    """
    return {"id": str(workspace.id), "tenant_id": str(workspace.tenant_id), "name": workspace.name}


def _workspace_from_replay(replay: tuple[str, dict[str, str | None]], digest: str) -> Workspace:
    """Validate and reconstruct a workspace from an idempotency record.

    Args:
        replay: Stored request digest and serialized workspace result.
        digest: Digest of the request currently being processed.

    Returns:
        Reconstructed workspace from the durable replay result.

    Raises:
        IdempotencyConflictError: If this key has different accepted input.
    """
    stored_digest, result = replay
    if stored_digest != digest:
        raise IdempotencyConflictError()
    return Workspace(
        _workspace_id(str(result["id"])),
        _tenant_id(str(result["tenant_id"])),
        str(result["name"]),
        "replayed",
    )


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


def _tenant_id(value: str) -> TenantId:
    """Rebuild the workspace owner identity without coupling to route parsing.

    Args:
        value: Serialized namespaced tenant identifier.

    Returns:
        Reconstructed tenant identity accepted by ``Workspace``.

    Raises:
        ValueError: If durable replay data has an invalid identifier shape.
    """
    namespace, separator, local_value = value.rpartition(":")
    if not separator:
        raise ValueError("invalid stored identifier")
    return TenantId(namespace, local_value)
