"""PostgreSQL mappings for provider-neutral identity and membership grants."""

from __future__ import annotations

from sqlalchemy import Connection, insert, select

from contour.infrastructure.postgres.tables.catalog import memberships, principals, tenants
from contour.tenancy.domain.access import Membership, Principal, PrincipalId
from contour.tenancy.domain.tenant import Tenant, TenantId


class PostgresPrincipalRepository:
    """Maps principals inside a caller-owned transaction."""

    def __init__(self, connection: Connection) -> None:
        """Bind the repository to its transaction connection."""
        self._connection = connection

    def get_principal(self, principal_id: PrincipalId) -> Principal | None:
        """Return an authenticated principal by stable identity, if recorded."""
        row = self._connection.execute(
            select(principals.c.namespace).where(
                principals.c.namespace == principal_id.namespace,
                principals.c.value == principal_id.value,
            )
        ).one_or_none()
        return None if row is None else Principal(principal_id)

    def save_principal(self, principal: Principal) -> None:
        """Insert one authenticated principal identity."""
        self._connection.execute(
            insert(principals).values(namespace=principal.id.namespace, value=principal.id.value)
        )


class PostgresMembershipRepository:
    """Maps uniform tenant grants inside a caller-owned transaction."""

    def __init__(self, connection: Connection) -> None:
        """Bind the repository to its transaction connection."""
        self._connection = connection

    def get_membership(self, principal_id: PrincipalId, tenant_id: TenantId) -> Membership | None:
        """Return one principal's exact tenant grant, if present."""
        row = self._connection.execute(
            select(memberships.c.principal_namespace).where(
                memberships.c.principal_namespace == principal_id.namespace,
                memberships.c.principal_value == principal_id.value,
                memberships.c.tenant_namespace == tenant_id.namespace,
                memberships.c.tenant_value == tenant_id.value,
            )
        ).one_or_none()
        return None if row is None else Membership(principal_id, tenant_id)

    def list_tenants(self, principal_id: PrincipalId) -> tuple[Tenant, ...]:
        """Return visible tenant records in stable identity order."""
        rows = self._connection.execute(
            select(tenants.c.namespace, tenants.c.value, tenants.c.name)
            .join(
                memberships,
                (memberships.c.tenant_namespace == tenants.c.namespace)
                & (memberships.c.tenant_value == tenants.c.value),
            )
            .where(
                memberships.c.principal_namespace == principal_id.namespace,
                memberships.c.principal_value == principal_id.value,
            )
            .order_by(tenants.c.namespace, tenants.c.value)
        ).mappings()
        return tuple(Tenant(TenantId(row["namespace"], row["value"]), row["name"]) for row in rows)

    def save_membership(self, membership: Membership) -> None:
        """Insert one membership grant."""
        self._connection.execute(
            insert(memberships).values(
                principal_namespace=membership.principal_id.namespace,
                principal_value=membership.principal_id.value,
                tenant_namespace=membership.tenant_id.namespace,
                tenant_value=membership.tenant_id.value,
            )
        )
