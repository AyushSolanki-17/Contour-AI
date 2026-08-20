"""PostgreSQL repository for logical source records."""

from __future__ import annotations

from typing import cast

from sqlalchemy import Connection, insert, select

from contour.domain.source import Source, SourceId
from contour.domain.workspace import WorkspaceId
from contour.infrastructure.postgres.tables.catalog import sources


class PostgresSourceRepository:
    """Maps logical source records in a caller-owned transaction."""

    def __init__(self, connection: Connection) -> None:
        """Bind the repository to its caller-owned transaction connection."""
        self._connection = connection

    def get_source(self, source_id: SourceId) -> Source | None:
        """Return a logical source by stable identity, if visible."""
        statement = select(sources).where(
            sources.c.namespace == source_id.namespace,
            sources.c.value == source_id.value,
        )
        row = self._connection.execute(statement).mappings().one_or_none()
        if row is None:
            return None
        return Source(
            SourceId(cast(str, row["namespace"]), cast(str, row["value"])),
            WorkspaceId(cast(str, row["workspace_namespace"]), cast(str, row["workspace_value"])),
            cast(str, row["canonical_locator"]),
            cast(str, row["source_type"]),
            cast(str, row["scope"]),
            cast(str | None, row["license"]),
            cast(str, row["data_classification"]),
        )

    def save_source(self, source: Source) -> None:
        """Insert a logical source and let constraints reject bad references."""
        statement = insert(sources).values(
            namespace=source.id.namespace,
            value=source.id.value,
            workspace_namespace=source.workspace_id.namespace,
            workspace_value=source.workspace_id.value,
            canonical_locator=source.canonical_locator,
            source_type=source.source_type,
            scope=source.scope,
            license=source.license,
            data_classification=source.data_classification,
        )
        self._connection.execute(statement)
