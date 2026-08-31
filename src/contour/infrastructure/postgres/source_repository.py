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

    def list_sources(self, access: AccessContext, workspace_id: WorkspaceId) -> tuple[Source, ...]:
        """Return workspace-visible sources in stable identity order."""
        rows = self._connection.execute(
            select(sources)
            .where(
                sources.c.tenant_namespace == access.tenant_id.namespace,
                sources.c.tenant_value == access.tenant_id.value,
                sources.c.workspace_namespace == workspace_id.namespace,
                sources.c.workspace_value == workspace_id.value,
            )
            .order_by(sources.c.namespace, sources.c.value)
        ).mappings()
        return tuple(self._map_source(row) for row in rows)

    def get_source_by_locator(
        self, access: AccessContext, workspace_id: WorkspaceId, connector_kind: str, locator: str
    ) -> Source | None:
        """Return a source by its workspace-local logical registration key."""
        row = (
            self._connection.execute(
                select(sources).where(
                    sources.c.tenant_namespace == access.tenant_id.namespace,
                    sources.c.tenant_value == access.tenant_id.value,
                    sources.c.workspace_namespace == workspace_id.namespace,
                    sources.c.workspace_value == workspace_id.value,
                    sources.c.source_type == connector_kind,
                    sources.c.canonical_locator == locator,
                )
            )
            .mappings()
            .one_or_none()
        )
        return None if row is None else self._map_source(row)

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

    @staticmethod
    def _map_source(row: object) -> Source:
        """Map one SQLAlchemy source row without leaking database types."""
        mapped = cast(dict[str, object], row)
        return Source(
            SourceId(cast(str, mapped["namespace"]), cast(str, mapped["value"])),
            TenantId(cast(str, mapped["tenant_namespace"]), cast(str, mapped["tenant_value"])),
            WorkspaceId(
                cast(str, mapped["workspace_namespace"]), cast(str, mapped["workspace_value"])
            ),
            cast(str, mapped["canonical_locator"]),
            cast(str, mapped["source_type"]),
            cast(str, mapped["scope"]),
            cast(str | None, mapped["license"]),
            cast(str, mapped["data_classification"]),
        )
