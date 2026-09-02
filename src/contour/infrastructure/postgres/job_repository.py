"""PostgreSQL repository for durable requested work."""

from __future__ import annotations

from datetime import datetime
from typing import cast

from sqlalchemy import Connection, insert, select

from contour.infrastructure.postgres.tables.execution import jobs
from contour.jobs.domain.job import Job, JobId, JobStatus
from contour.tenancy.domain.access import AccessContext
from contour.tenancy.domain.tenant import TenantId
from contour.time import TimePoint
from contour.workspaces.domain.workspace import WorkspaceId


class PostgresJobRepository:
    """Maps durable job requests in a caller-owned transaction."""

    def __init__(self, connection: Connection) -> None:
        """Bind the repository to its caller-owned transaction connection."""
        self._connection = connection

    def get_job(self, access: AccessContext, job_id: JobId) -> Job | None:
        """Return a durable job including its explicit lifecycle state."""
        row = (
            self._connection.execute(
                select(jobs).where(
                    jobs.c.namespace == job_id.namespace,
                    jobs.c.value == job_id.value,
                    jobs.c.tenant_namespace == access.tenant_id.namespace,
                    jobs.c.tenant_value == access.tenant_id.value,
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return None
        return Job(
            job_id,
            TenantId(cast(str, row["tenant_namespace"]), cast(str, row["tenant_value"])),
            WorkspaceId(cast(str, row["workspace_namespace"]), cast(str, row["workspace_value"])),
            cast(str, row["kind"]),
            TimePoint(cast(datetime | None, row["requested_at"])),
            cast(JobStatus, row["status"]),
        )

    def save_job(self, access: AccessContext, job: Job) -> None:
        """Insert a durable request and let constraints reject conflicts or orphans."""
        if not access.permits(job.tenant_id):
            raise ValueError("job is outside access scope")
        self._connection.execute(
            insert(jobs).values(
                namespace=job.id.namespace,
                value=job.id.value,
                tenant_namespace=job.tenant_id.namespace,
                tenant_value=job.tenant_id.value,
                workspace_namespace=job.workspace_id.namespace,
                workspace_value=job.workspace_id.value,
                kind=job.kind,
                requested_at=job.requested_at.value,
                status=job.status,
            )
        )
