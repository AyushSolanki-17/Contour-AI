"""Application orchestration for catalog admission."""

from __future__ import annotations

from contour.domain.evidence import EvidenceId, EvidenceLocator
from contour.domain.source import Source
from contour.domain.source_version import SourceVersion
from contour.domain.tenant import Tenant
from contour.domain.workspace import Workspace
from contour.repositories.catalog_transaction import CatalogTransactionManager


class CatalogAdmissionService:
    """Admits one coherent workspace, source, version, and exact evidence record."""

    def __init__(self, transactions: CatalogTransactionManager) -> None:
        """Initialize the service with the catalog transaction boundary."""
        self._transactions = transactions

    def admit(
        self,
        *,
        tenant: Tenant,
        workspace: Workspace,
        source: Source,
        version: SourceVersion,
        evidence_id: EvidenceId,
        evidence: EvidenceLocator,
    ) -> None:
        """Persist an internally consistent catalog record set atomically.

        Raises:
            ValueError: If a record does not share its enclosing Tenant and Workspace.
        """
        if workspace.tenant_id != tenant.id:
            raise ValueError("workspace must belong to the admitted tenant")
        if source.tenant_id != tenant.id:
            raise ValueError("source must belong to the admitted tenant")
        if source.workspace_id != workspace.id:
            raise ValueError("source must belong to the admitted workspace")
        if version.tenant_id != tenant.id or version.workspace_id != workspace.id:
            raise ValueError("source version must belong to the admitted tenant and workspace")
        if version.source_id != source.id:
            raise ValueError("source version must belong to the admitted source")
        if evidence.tenant_id != tenant.id or evidence.workspace_id != workspace.id:
            raise ValueError("evidence must belong to the admitted tenant and workspace")
        if evidence.source_version_id != version.id:
            raise ValueError("evidence must belong to the admitted source version")

        with self._transactions.transaction() as transaction:
            transaction.tenants.save_tenant(tenant)
            transaction.workspaces.save_workspace(workspace)
            transaction.sources.save_source(source)
            transaction.source_versions.save_source_version(version)
            transaction.evidence.save_evidence(evidence_id, evidence)
