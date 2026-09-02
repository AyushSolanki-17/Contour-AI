"""Application orchestration for catalog admission."""

from __future__ import annotations

from contour.errors import ResourceNotFoundError
from contour.knowledge.domain.evidence import EvidenceId, EvidenceLocator
from contour.sources.domain.source import Source
from contour.sources.domain.source_version import SourceVersion
from contour.tenancy.application.catalog_store import CatalogTransactionManager
from contour.tenancy.domain.access import AccessContext
from contour.tenancy.domain.tenant import Tenant
from contour.workspaces.domain.workspace import Workspace


class CatalogAdmissionService:
    """Admits one coherent workspace, source, version, and exact evidence record."""

    def __init__(self, transactions: CatalogTransactionManager) -> None:
        """Initialize the service with the catalog transaction boundary."""
        self._transactions = transactions

    def admit(
        self,
        *,
        access: AccessContext,
        tenant: Tenant,
        workspace: Workspace,
        source: Source,
        version: SourceVersion,
        evidence_id: EvidenceId,
        evidence: EvidenceLocator,
    ) -> None:
        """Persist an internally consistent catalog record set atomically.

        Raises:
            ResourceNotFoundError: If the scope or any nested record is inaccessible.
        """
        if not access.permits(tenant.id):
            raise ResourceNotFoundError()
        if workspace.tenant_id != tenant.id:
            raise ResourceNotFoundError()
        if source.tenant_id != tenant.id:
            raise ResourceNotFoundError()
        if source.workspace_id != workspace.id:
            raise ResourceNotFoundError()
        if version.tenant_id != tenant.id or version.workspace_id != workspace.id:
            raise ResourceNotFoundError()
        if version.source_id != source.id:
            raise ResourceNotFoundError()
        if evidence.tenant_id != tenant.id or evidence.workspace_id != workspace.id:
            raise ResourceNotFoundError()
        if evidence.source_version_id != version.id:
            raise ResourceNotFoundError()

        with self._transactions.transaction() as transaction:
            transaction.workspaces.save_workspace(access, workspace)
            transaction.sources.save_source(access, source)
            transaction.source_versions.save_source_version(access, version)
            transaction.evidence.save_evidence(access, evidence_id, evidence)
