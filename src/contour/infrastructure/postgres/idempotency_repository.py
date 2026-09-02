"""PostgreSQL persistence for scoped application operation results."""

from __future__ import annotations

from typing import cast

from sqlalchemy import Connection, insert, select

from contour.infrastructure.postgres.tables.catalog import idempotency_records
from contour.tenancy.domain.access import Principal


class PostgresIdempotencyRepository:
    """Maps replay records inside the caller's catalog transaction."""

    def __init__(self, connection: Connection) -> None:
        """Bind the repository to its caller-owned transaction connection."""
        self._connection = connection

    def get_result(
        self, principal: Principal, scope: str, operation: str, key: str
    ) -> tuple[str, dict[str, str | None]] | None:
        """Return the accepted input digest and operation result for an exact key."""
        row = self._connection.execute(
            select(idempotency_records.c.payload_digest, idempotency_records.c.response).where(
                idempotency_records.c.principal_namespace == principal.id.namespace,
                idempotency_records.c.principal_value == principal.id.value,
                idempotency_records.c.scope == scope,
                idempotency_records.c.route == operation,
                idempotency_records.c.key == key,
            )
        ).one_or_none()
        if row is None:
            return None
        return cast(str, row.payload_digest), cast(dict[str, str | None], row.response)

    def save_result(
        self,
        principal: Principal,
        scope: str,
        operation: str,
        key: str,
        payload_digest: str,
        result: dict[str, str | None],
    ) -> None:
        """Insert one result before the containing transaction commits."""
        self._connection.execute(
            insert(idempotency_records).values(
                principal_namespace=principal.id.namespace,
                principal_value=principal.id.value,
                scope=scope,
                route=operation,
                key=key,
                payload_digest=payload_digest,
                response=result,
            )
        )
