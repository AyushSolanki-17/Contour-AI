"""PostgreSQL repository for durable requested work."""

from __future__ import annotations

from datetime import datetime
from typing import cast

from sqlalchemy import Connection, insert, select

from contour.domain.job import Job, JobId, JobStatus
from contour.domain.time_point import TimePoint
from contour.domain.workspace import WorkspaceId
from contour.infrastructure.postgres.tables.knowledge import jobs


class PostgresJobRepository:
    """Maps durable job requests in a caller-owned transaction."""

    def __init__(self, connection: Connection) -> None:
        """Bind the repository to its caller-owned transaction connection."""
        self._connection = connection

    def get_job(self, job_id: JobId) -> Job | None:
        """Return a durable job including its explicit lifecycle state."""
        row = (
            self._connection.execute(
                select(jobs).where(
                    jobs.c.namespace == job_id.namespace, jobs.c.value == job_id.value
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return None
        return Job(
            job_id,
            WorkspaceId(cast(str, row["workspace_namespace"]), cast(str, row["workspace_value"])),
            cast(str, row["kind"]),
            TimePoint(cast(datetime | None, row["requested_at"])),
            cast(JobStatus, row["status"]),
        )

    def save_job(self, job: Job) -> None:
        """Insert a durable request and let constraints reject conflicts or orphans."""
        self._connection.execute(
            insert(jobs).values(
                namespace=job.id.namespace,
                value=job.id.value,
                workspace_namespace=job.workspace_id.namespace,
                workspace_value=job.workspace_id.value,
                kind=job.kind,
                requested_at=job.requested_at.value,
                status=job.status,
            )
        )
