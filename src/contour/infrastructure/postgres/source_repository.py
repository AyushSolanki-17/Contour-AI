"""PostgreSQL repository for logical source records."""

from __future__ import annotations

from typing import cast

from sqlalchemy import Connection, insert, select

from contour.domain.access import AccessContext
from contour.domain.source import Source, SourceId
from contour.domain.tenant import TenantId
from contour.domain.workspace import WorkspaceId
from contour.infrastructure.postgres.tables.catalog import sources


class PostgresSourceRepository:
    """Maps logical source records in a caller-owned transaction."""

    def __init__(self, connection: Connection) -> None:
        """Bind the repository to its caller-owned transaction connection."""
        self._connection = connection

    def get_source(self, access: AccessContext, source_id: SourceId) -> Source | None:
        """Return a logical source by stable identity, if visible."""
        statement = select(sources).where(
            sources.c.namespace == source_id.namespace,
            sources.c.value == source_id.value,
            sources.c.tenant_namespace == access.tenant_id.namespace,
            sources.c.tenant_value == access.tenant_id.value,
        )
        row = self._connection.execute(statement).mappings().one_or_none()
        if row is None:
            return None
        return Source(
            SourceId(cast(str, row["namespace"]), cast(str, row["value"])),
            TenantId(cast(str, row["tenant_namespace"]), cast(str, row["tenant_value"])),
            WorkspaceId(cast(str, row["workspace_namespace"]), cast(str, row["workspace_value"])),
            cast(str, row["canonical_locator"]),
            cast(str, row["source_type"]),
            cast(str, row["scope"]),
            cast(str | None, row["license"]),
            cast(str, row["data_classification"]),
        )

    def save_source(self, access: AccessContext, source: Source) -> None:
        """Insert a logical source and let constraints reject bad references."""
        if not access.permits(source.tenant_id):
            raise ValueError("source is outside access scope")
        statement = insert(sources).values(
            namespace=source.id.namespace,
            value=source.id.value,
            tenant_namespace=source.tenant_id.namespace,
            tenant_value=source.tenant_id.value,
            workspace_namespace=source.workspace_id.namespace,
            workspace_value=source.workspace_id.value,
            canonical_locator=source.canonical_locator,
            source_type=source.source_type,
            scope=source.scope,
            license=source.license,
            data_classification=source.data_classification,
        )
        self._connection.execute(statement)
