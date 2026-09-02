"""Authenticated tenant collection use cases and replay handling."""

from __future__ import annotations

from hashlib import sha256
from json import dumps
from uuid import uuid4

from contour.domain.access import AccessContext, Membership, Principal
from contour.domain.tenant import Tenant, TenantId
from contour.repositories.catalog_transaction import CatalogTransactionManager
from contour.services.access_service import TenantAccessService
from contour.services.catalog_errors import CatalogConflictError, IdempotencyConflictError


class TenantCollectionService:
    """Own authenticated tenant creation, visibility, and scope selection.

    The service owns tenant-level idempotency because creating a tenant also
    creates its initiating membership in the same transaction.
    """

    def __init__(self, transactions: CatalogTransactionManager) -> None:
        """Bind the transaction boundary used by tenant operations.

        Args:
            transactions: Catalog persistence contract for tenant and membership writes.
        """
        self._transactions = transactions
        self._access = TenantAccessService(transactions)

    def create_tenant(self, principal: Principal, name: str, key: str) -> tuple[Tenant, bool]:
        """Create or replay a tenant with its initiating membership atomically.

        Args:
            principal: Authenticated subject that will own the initial membership.
            name: Validated tenant display name.
            key: Client idempotency key for this creation request.

        Returns:
            The accepted tenant and whether it was recovered from a replay.

        Raises:
            IdempotencyConflictError: If the key was first used for different input.
        """
        digest = _payload_digest(name)
        try:
            with self._transactions.transaction() as transaction:
                replay = transaction.idempotency.get_result(principal, "global", "tenants", key)
                if replay is not None:
                    return _tenant_from_replay(replay, digest), True
                if transaction.principals.get_principal(principal.id) is None:
                    transaction.principals.save_principal(principal)
                tenant = Tenant(TenantId("TENANT", str(uuid4())), name)
                transaction.tenants.save_tenant(tenant)
                transaction.memberships.save_membership(Membership(principal.id, tenant.id))
                transaction.idempotency.save_result(
                    principal, "global", "tenants", key, digest, _tenant_result(tenant)
                )
        except CatalogConflictError:
            replayed = self._replay(principal, key, digest)
            if replayed is None:
                raise
            return replayed, True
        return tenant, False

    def list_tenants(self, principal: Principal) -> tuple[Tenant, ...]:
        """Return only tenants visible through the principal's memberships.

        Args:
            principal: Authenticated subject whose durable grants are queried.

        Returns:
            Tenant values in repository-defined deterministic order.
        """
        return self._access.list_tenants(principal=principal)

    def open_tenant(
        self, principal: Principal, tenant_id: TenantId, correlation_id: str
    ) -> AccessContext:
        """Verify a tenant selector without revealing foreign tenant existence.

        Args:
            principal: Authenticated subject selecting a tenant.
            tenant_id: Tenant selector supplied by the delivery adapter.
            correlation_id: Non-secret request identifier retained in access context.

        Returns:
            Verified principal and membership scope.

        Raises:
            ResourceNotFoundError: If the principal cannot access the selected tenant.
        """
        return self._access.open_tenant(
            principal=principal, tenant_id=tenant_id, correlation_id=correlation_id
        )

    def _replay(self, principal: Principal, key: str, digest: str) -> Tenant | None:
        """Read a concurrent winner's durable tenant result.

        Args:
            principal: Subject that owns the idempotency namespace.
            key: Idempotency key that may have concurrently committed.
            digest: Canonical request digest required for replay equivalence.

        Returns:
            The accepted tenant when a concurrent request committed, otherwise ``None``.
        """
        with self._transactions.transaction() as transaction:
            replay = transaction.idempotency.get_result(principal, "global", "tenants", key)
        return None if replay is None else _tenant_from_replay(replay, digest)


def _payload_digest(name: str) -> str:
    """Create the stable tenant-request digest used for idempotency comparison.

    Args:
        name: Validated tenant name supplied by the client.

    Returns:
        SHA-256 digest over canonical JSON input.
    """
    return sha256(dumps({"name": name}, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _tenant_result(tenant: Tenant) -> dict[str, str | None]:
    """Serialize the durable tenant fields needed to reconstruct a replay.

    Args:
        tenant: Newly accepted tenant.

    Returns:
        JSON-safe result stored beside the idempotency key.
    """
    return {"id": str(tenant.id), "name": tenant.name}


def _tenant_from_replay(replay: tuple[str, dict[str, str | None]], digest: str) -> Tenant:
    """Validate and reconstruct a tenant from an idempotency record.

    Args:
        replay: Stored request digest and serialized tenant result.
        digest: Digest of the request currently being processed.

    Returns:
        Reconstructed tenant from the durable replay result.

    Raises:
        IdempotencyConflictError: If this key has different accepted input.
    """
    stored_digest, result = replay
    if stored_digest != digest:
        raise IdempotencyConflictError()
    return Tenant(_tenant_id(str(result["id"])), str(result["name"]))


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
