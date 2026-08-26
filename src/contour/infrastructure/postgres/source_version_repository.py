"""PostgreSQL repository for immutable source-version records."""

from __future__ import annotations

from datetime import datetime
from typing import cast

from sqlalchemy import Connection, insert, select

from contour.domain.source_version import SourceVersion, SourceVersionId
from contour.domain.time_point import TimePoint
from contour.infrastructure.postgres.tables.catalog import source_versions


class PostgresSourceVersionRepository:
    """Maps immutable source versions in a caller-owned transaction."""

    def __init__(self, connection: Connection) -> None:
        """Bind the repository to its caller-owned transaction connection."""
        self._connection = connection

    def get_source_version(self, version_id: SourceVersionId) -> SourceVersion | None:
        """Return an immutable source version by content identity."""
        statement = select(
            source_versions.c.observed_at,
            source_versions.c.upstream_revision,
            source_versions.c.source_time,
            source_versions.c.revision_time,
        ).where(
            source_versions.c.source_namespace == version_id.source_id.namespace,
            source_versions.c.source_value == version_id.source_id.value,
            source_versions.c.content_digest == version_id.content_digest.value,
        )
        row = self._connection.execute(statement).mappings().one_or_none()
        if row is None:
            return None
        return SourceVersion(
            version_id,
            version_id.source_id,
            version_id.content_digest,
            TimePoint(cast(datetime | None, row["observed_at"])),
            cast(str | None, row["upstream_revision"]),
            TimePoint(cast(datetime | None, row["source_time"])),
            TimePoint(cast(datetime | None, row["revision_time"])),
        )

    def save_source_version(self, version: SourceVersion) -> None:
        """Insert immutable version metadata without replacing prior content."""
        statement = insert(source_versions).values(
            source_namespace=version.source_id.namespace,
            source_value=version.source_id.value,
            content_digest=version.content_digest.value,
            observed_at=version.observed_at.value,
            observation_time_unknown=not version.observed_at.is_known,
            upstream_revision=version.upstream_revision,
            source_time=version.source_time.value,
            revision_time=version.revision_time.value,
        )
        self._connection.execute(statement)
