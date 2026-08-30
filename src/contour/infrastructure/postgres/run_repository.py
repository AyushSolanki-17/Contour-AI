"""PostgreSQL repository for durable execution attempts."""

from __future__ import annotations

from datetime import datetime
from typing import cast

from sqlalchemy import Connection, insert, select

from contour.domain.job import JobId
from contour.domain.run import Run, RunId, RunStatus
from contour.domain.tenant import TenantId
from contour.domain.time_point import TimePoint
from contour.domain.workspace import WorkspaceId
from contour.infrastructure.postgres.tables.knowledge import runs


class PostgresRunRepository:
    """Maps job execution attempts in a caller-owned transaction."""

    def __init__(self, connection: Connection) -> None:
        """Bind the repository to its caller-owned transaction connection."""
        self._connection = connection

    def get_run(self, run_id: RunId) -> Run | None:
        """Return a run attempt including its terminal or active lifecycle state."""
        row = (
            self._connection.execute(
                select(runs).where(
                    runs.c.namespace == run_id.namespace, runs.c.value == run_id.value
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return None
        return Run(
            run_id,
            TenantId(cast(str, row["tenant_namespace"]), cast(str, row["tenant_value"])),
            WorkspaceId(cast(str, row["workspace_namespace"]), cast(str, row["workspace_value"])),
            JobId(cast(str, row["job_namespace"]), cast(str, row["job_value"])),
            TimePoint(cast(datetime | None, row["started_at"])),
            cast(RunStatus, row["status"]),
        )

    def save_run(self, run: Run) -> None:
        """Insert one distinct attempt linked by foreign key to its job request."""
        self._connection.execute(
            insert(runs).values(
                namespace=run.id.namespace,
                value=run.id.value,
                tenant_namespace=run.tenant_id.namespace,
                tenant_value=run.tenant_id.value,
                workspace_namespace=run.workspace_id.namespace,
                workspace_value=run.workspace_id.value,
                job_namespace=run.job_id.namespace,
                job_value=run.job_id.value,
                started_at=run.started_at.value,
                status=run.status,
            )
        )
