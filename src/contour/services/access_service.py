"""Application use cases for verified tenant access contexts."""

from __future__ import annotations

from contour.domain.access import AccessContext, Membership, Principal
from contour.domain.tenant import Tenant, TenantId
from contour.repositories.catalog_transaction import CatalogTransactionManager
from contour.services.access_errors import ResourceNotFoundError


class TenantAccessService:
    """Creates tenant memberships and verifies a principal's selected scope."""

    def __init__(self, transactions: CatalogTransactionManager) -> None:
        """Initialize the service with the identity-capable catalog boundary."""
        self._transactions = transactions

    def bootstrap_tenant(
        self, *, principal: Principal, tenant: Tenant, correlation_id: str
    ) -> AccessContext:
        """Atomically create a tenant and its initiator membership.

        Raises:
            CatalogConflictError: If either identity or membership is already accepted.
        """
        membership = Membership(principal.id, tenant.id)
        with self._transactions.transaction() as transaction:
            if transaction.principals.get_principal(principal.id) is None:
                transaction.principals.save_principal(principal)
            transaction.tenants.save_tenant(tenant)
            transaction.memberships.save_membership(membership)
        return AccessContext(principal, membership, correlation_id)

    def list_tenants(self, *, principal: Principal) -> tuple[Tenant, ...]:
        """Return only tenants for which the principal has a durable membership."""
        with self._transactions.transaction() as transaction:
            return transaction.memberships.list_tenants(principal.id)

    def open_tenant(
        self, *, principal: Principal, tenant_id: TenantId, correlation_id: str
    ) -> AccessContext:
        """Verify a selected tenant without revealing foreign tenant existence.

        Raises:
            ResourceNotFoundError: If the principal lacks the selected membership.
        """
        with self._transactions.transaction() as transaction:
            membership = transaction.memberships.get_membership(principal.id, tenant_id)
        if membership is None:
            raise ResourceNotFoundError()
        return AccessContext(principal, membership, correlation_id)
