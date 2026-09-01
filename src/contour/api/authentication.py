"""HTTP credential-verification contract for authenticated delivery."""

from __future__ import annotations

from typing import Protocol

from contour.domain.access import Principal
from contour.services.error import ApplicationError


class UnauthenticatedError(ApplicationError):
    """Signal that HTTP delivery could not verify a bearer credential."""

    def __init__(self) -> None:
        """Create a credential-safe authentication outcome."""
        super().__init__(code="auth.unauthenticated", message="Authentication is required.")


class CredentialVerifier(Protocol):
    """Verifies an HTTP bearer credential without exposing credential material."""

    def verify(self, credential: str) -> Principal | None:
        """Return the verified principal, or ``None`` for an invalid credential."""
