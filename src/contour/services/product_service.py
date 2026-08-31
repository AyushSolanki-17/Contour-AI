"""Authenticated tenant, workspace, and source collection use cases."""

from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
from json import dumps
from uuid import uuid4

from contour.domain.access import AccessContext, Principal
from contour.domain.source import Source, SourceId
from contour.domain.tenant import Tenant, TenantId
from contour.domain.workspace import Workspace, WorkspaceId
from contour.repositories.catalog_transaction import CatalogTransactionManager
from contour.services.access_errors import ResourceNotFoundError
from contour.services.access_service import TenantAccessService
from contour.services.product_errors import (
    IdempotencyConflictError,
    SourceAlreadyRegisteredError,
    UnsupportedConnectorError,
)


class ProductCatalogService:
    """Orchestrates the first source-neutral authenticated product collections."""

    def __init__(
        self, transactions: CatalogTransactionManager, supported_connectors: frozenset[str]
    ) -> None:
        """Bind catalog persistence and explicitly admitted connector capabilities."""
        self._transactions = transactions
        self._access = TenantAccessService(transactions)
        self._supported_connectors = supported_connectors

    def create_tenant(
        self, principal: Principal, name: str, correlation_id: str, key: str
    ) -> tuple[Tenant, bool]:
        """Create or replay a tenant and its initial membership atomically."""
        digest = _payload_digest({"name": name})
        with self._transactions.transaction() as transaction:
            replay = transaction.idempotency.get_response(principal, "global", "tenants", key)
            if replay is not None:
                return _tenant_from_response(replay, digest), True
            if transaction.principals.get_principal(principal.id) is None:
                transaction.principals.save_principal(principal)
            tenant = Tenant(TenantId("TENANT", str(uuid4())), name)
            transaction.tenants.save_tenant(tenant)
            from contour.domain.access import Membership

            transaction.memberships.save_membership(Membership(principal.id, tenant.id))
            transaction.idempotency.save_response(
                principal, "global", "tenants", key, digest, _tenant_response(tenant)
            )
        return tenant, False

    def list_tenants(self, principal: Principal) -> tuple[Tenant, ...]:
        """Return only tenants visible through the principal's memberships."""
        return self._access.list_tenants(principal=principal)

    def open_tenant(
        self, principal: Principal, tenant_id: TenantId, correlation_id: str
    ) -> AccessContext:
        """Verify a tenant selector without enumerating foreign tenants."""
        return self._access.open_tenant(
            principal=principal, tenant_id=tenant_id, correlation_id=correlation_id
        )

    def create_workspace(
        self, access: AccessContext, name: str, key: str, payload: dict[str, str]
    ) -> tuple[Workspace, bool]:
        """Create or replay one tenant-scoped workspace creation request."""
        digest = _payload_digest(payload)
        route = "workspaces"
        with self._transactions.transaction() as transaction:
            replay = transaction.idempotency.get_response(
                access.principal, str(access.tenant_id), route, key
            )
            if replay is not None:
                return _workspace_from_response(replay, digest), True
            workspace = Workspace(
                WorkspaceId("WORKSPACE", str(uuid4())),
                access.tenant_id,
                name,
                str(access.principal.id),
            )
            response = _workspace_response(workspace)
            transaction.workspaces.save_workspace(access, workspace)
            transaction.idempotency.save_response(
                access.principal, str(access.tenant_id), route, key, digest, response
            )
        return workspace, False

    def list_workspaces(self, access: AccessContext) -> tuple[Workspace, ...]:
        """Return workspaces only from the selected verified tenant."""
        with self._transactions.transaction() as transaction:
            return transaction.workspaces.list_workspaces(access)

    def create_source(
        self,
        access: AccessContext,
        workspace_id: WorkspaceId,
        values: dict[str, str | None],
        key: str,
    ) -> tuple[Source, bool]:
        """Register or replay one source in an accessible workspace.

        Raises:
            ResourceNotFoundError: If the workspace is absent or foreign.
            UnsupportedConnectorError: If the connector is not admitted.
            SourceAlreadyRegisteredError: If the source registration already exists.
        """
        connector_kind = str(values["connector_kind"])
        if connector_kind not in self._supported_connectors:
            raise UnsupportedConnectorError()
        digest = _payload_digest(values)
        route = f"sources:{workspace_id}"
        with self._transactions.transaction() as transaction:
            if transaction.workspaces.get_workspace(access, workspace_id) is None:
                raise ResourceNotFoundError()
            replay = transaction.idempotency.get_response(
                access.principal, str(access.tenant_id), route, key
            )
            if replay is not None:
                return _source_from_response(replay, digest), True
            locator = str(values["canonical_locator"])
            if transaction.sources.get_source_by_locator(
                access, workspace_id, connector_kind, locator
            ):
                raise SourceAlreadyRegisteredError()
            source = Source(
                SourceId("SOURCE", str(uuid4())),
                access.tenant_id,
                workspace_id,
                locator,
                connector_kind,
                str(values["scope"]),
                values["license"],
                str(values["data_classification"]),
            )
            response = _source_response(source)
            transaction.sources.save_source(access, source)
            transaction.idempotency.save_response(
                access.principal, str(access.tenant_id), route, key, digest, response
            )
        return source, False

    def list_sources(self, access: AccessContext, workspace_id: WorkspaceId) -> tuple[Source, ...]:
        """Return sources only after confirming the nested workspace is accessible."""
        with self._transactions.transaction() as transaction:
            if transaction.workspaces.get_workspace(access, workspace_id) is None:
                raise ResourceNotFoundError()
            return transaction.sources.list_sources(access, workspace_id)


def _payload_digest(payload: Mapping[str, str | None]) -> str:
    """Create a canonical digest for replay-equivalence comparison."""
    return sha256(dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _workspace_response(workspace: Workspace) -> dict[str, str | None]:
    """Serialize the durable workspace fields retained by an idempotency record."""
    return {"id": str(workspace.id), "tenant_id": str(workspace.tenant_id), "name": workspace.name}


def _tenant_response(tenant: Tenant) -> dict[str, str | None]:
    """Serialize the durable tenant fields retained by an idempotency record."""
    return {"id": str(tenant.id), "name": tenant.name}


def _source_response(source: Source) -> dict[str, str | None]:
    """Serialize the durable source fields retained by an idempotency record."""
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


def _workspace_from_response(replay: tuple[str, dict[str, str | None]], digest: str) -> Workspace:
    """Validate and rebuild a workspace result from a durable replay record."""
    stored_digest, result = replay
    if stored_digest != digest:
        raise IdempotencyConflictError()
    return Workspace(
        _workspace_id(str(result["id"])),
        _tenant_id(str(result["tenant_id"])),
        str(result["name"]),
        "replayed",
    )


def _tenant_from_response(replay: tuple[str, dict[str, str | None]], digest: str) -> Tenant:
    """Validate and rebuild a tenant result from a durable replay record."""
    stored_digest, result = replay
    if stored_digest != digest:
        raise IdempotencyConflictError()
    return Tenant(_tenant_id(str(result["id"])), str(result["name"]))


def _source_from_response(replay: tuple[str, dict[str, str | None]], digest: str) -> Source:
    """Validate and rebuild a source result from a durable replay record."""
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


def _parts(value: str) -> tuple[str, str]:
    """Split a serialized namespaced identifier accepted from internal replay data."""
    namespace, separator, local_value = value.rpartition(":")
    if not separator:
        raise ValueError("invalid stored identifier")
    return namespace, local_value


def _tenant_id(value: str) -> TenantId:
    """Rebuild a tenant identity from internal idempotency data."""
    return TenantId(*_parts(value))


def _workspace_id(value: str) -> WorkspaceId:
    """Rebuild a workspace identity from internal idempotency data."""
    return WorkspaceId(*_parts(value))


def _source_id(value: str) -> SourceId:
    """Rebuild a source identity from internal idempotency data."""
    return SourceId(*_parts(value))
