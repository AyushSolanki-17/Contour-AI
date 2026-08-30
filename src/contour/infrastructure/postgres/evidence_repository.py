"""PostgreSQL repository for exact evidence locators."""

from __future__ import annotations

from typing import cast

from sqlalchemy import Connection, insert, select

from contour.domain.evidence import EvidenceId, EvidenceLocator
from contour.domain.source import SourceId
from contour.domain.source_version import ContentDigest, SourceVersionId
from contour.domain.tenant import TenantId
from contour.domain.workspace import WorkspaceId
from contour.infrastructure.postgres.tables.catalog import evidence


class PostgresEvidenceRepository:
    """Maps exact evidence locators in a caller-owned transaction."""

    def __init__(self, connection: Connection) -> None:
        """Bind the repository to its caller-owned transaction connection."""
        self._connection = connection

    def get_evidence(self, evidence_id: EvidenceId) -> EvidenceLocator | None:
        """Return evidence with its immutable source-version identity."""
        statement = select(
            evidence.c.tenant_namespace,
            evidence.c.tenant_value,
            evidence.c.workspace_namespace,
            evidence.c.workspace_value,
            evidence.c.source_namespace,
            evidence.c.source_value,
            evidence.c.content_digest,
            evidence.c.locator,
            evidence.c.start_offset,
            evidence.c.end_offset,
        ).where(
            evidence.c.namespace == evidence_id.namespace,
            evidence.c.value == evidence_id.value,
        )
        row = self._connection.execute(statement).mappings().one_or_none()
        if row is None:
            return None
        version_id = SourceVersionId(
            SourceId(cast(str, row["source_namespace"]), cast(str, row["source_value"])),
            ContentDigest(cast(str, row["content_digest"])),
        )
        return EvidenceLocator(
            TenantId(cast(str, row["tenant_namespace"]), cast(str, row["tenant_value"])),
            WorkspaceId(cast(str, row["workspace_namespace"]), cast(str, row["workspace_value"])),
            version_id,
            cast(str, row["locator"]),
            cast(int | None, row["start_offset"]),
            cast(int | None, row["end_offset"]),
        )

    def save_evidence(self, evidence_id: EvidenceId, locator: EvidenceLocator) -> None:
        """Insert exact evidence bound by foreign key to one source version."""
        version_id = locator.source_version_id
        statement = insert(evidence).values(
            namespace=evidence_id.namespace,
            value=evidence_id.value,
            tenant_namespace=locator.tenant_id.namespace,
            tenant_value=locator.tenant_id.value,
            workspace_namespace=locator.workspace_id.namespace,
            workspace_value=locator.workspace_id.value,
            source_namespace=version_id.source_id.namespace,
            source_value=version_id.source_id.value,
            content_digest=version_id.content_digest.value,
            locator=locator.locator,
            start_offset=locator.start_offset,
            end_offset=locator.end_offset,
        )
        self._connection.execute(statement)
