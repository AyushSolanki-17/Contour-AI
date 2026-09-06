"""Dependencies shared by the HTTP delivery adapter."""

from __future__ import annotations

from dataclasses import dataclass

from contour.api.authentication import CredentialVerifier
from contour.api.cursor import CursorCodec
from contour.api.health import HealthService
from contour.sources.application.registration import SourceCollectionService
from contour.tenancy.application.collections import TenantCollectionService
from contour.workspaces.application.collections import WorkspaceCollectionService


@dataclass(frozen=True, slots=True)
class ApiDependencies:
    """Fully constructed application services required by public HTTP routes.

    The composition root creates this object once per process. Routes receive
    the bundle as a delivery dependency and never construct services or
    infrastructure adapters themselves.
    """

    health: HealthService
    tenants: TenantCollectionService
    workspaces: WorkspaceCollectionService
    sources: SourceCollectionService
    credentials: CredentialVerifier
    cursors: CursorCodec
