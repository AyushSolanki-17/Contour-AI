"""PostgreSQL repository for workspace records."""

from __future__ import annotations

from typing import cast

from sqlalchemy import Connection, insert, select

from contour.domain.tenant import TenantId
from contour.domain.workspace import Workspace, WorkspaceId
from contour.infrastructure.postgres.tables.catalog import workspaces


class PostgresWorkspaceRepository:
    """Maps workspace domain records in a caller-owned transaction."""

    def __init__(self, connection: Connection) -> None:
        """Bind the repository to its caller-owned transaction connection."""
        self._connection = connection

    def get_workspace(self, workspace_id: WorkspaceId) -> Workspace | None:
        """Return a workspace by stable identity, if the transaction can see it."""
        statement = select(workspaces).where(
            workspaces.c.namespace == workspace_id.namespace,
            workspaces.c.value == workspace_id.value,
        )
        row = self._connection.execute(statement).mappings().one_or_none()
        if row is None:
            return None
        return Workspace(
            WorkspaceId(cast(str, row["namespace"]), cast(str, row["value"])),
            TenantId(cast(str, row["tenant_namespace"]), cast(str, row["tenant_value"])),
            cast(str, row["name"]),
            cast(str, row["owner_name"]),
            tuple((item[0], item[1]) for item in cast(list[list[str]], row["settings"])),
        )

    def save_workspace(self, workspace: Workspace) -> None:
        """Insert a workspace and let database constraints reject conflicts."""
        statement = insert(workspaces).values(
            namespace=workspace.id.namespace,
            value=workspace.id.value,
            tenant_namespace=workspace.tenant_id.namespace,
            tenant_value=workspace.tenant_id.value,
            name=workspace.name,
            owner_name=workspace.owner,
            settings=list(workspace.settings),
        )
        self._connection.execute(statement)
