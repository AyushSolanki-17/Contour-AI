"""PostgreSQL repository for durable tenant records."""

from __future__ import annotations

from typing import cast

from sqlalchemy import Connection, insert, select

from contour.infrastructure.postgres.tables.catalog import tenants
from contour.tenancy.domain.tenant import Tenant, TenantId


class PostgresTenantRepository:
    """Maps tenant domain records in a caller-owned transaction."""

    def __init__(self, connection: Connection) -> None:
        """Bind the repository to its caller-owned transaction connection."""
        self._connection = connection

    def get_tenant(self, tenant_id: TenantId) -> Tenant | None:
        """Return a tenant by stable identity, if the transaction can see it."""
        row = (
            self._connection.execute(
                select(tenants).where(
                    tenants.c.namespace == tenant_id.namespace,
                    tenants.c.value == tenant_id.value,
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return None
        return Tenant(
            TenantId(cast(str, row["namespace"]), cast(str, row["value"])),
            cast(str, row["name"]),
        )

    def save_tenant(self, tenant: Tenant) -> None:
        """Insert a tenant and let database constraints reject conflicts."""
        self._connection.execute(
            insert(tenants).values(
                namespace=tenant.id.namespace,
                value=tenant.id.value,
                name=tenant.name,
            )
        )
