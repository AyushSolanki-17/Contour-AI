"""HTTP credential-verification contract for authenticated delivery."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from fastapi import Header

from contour.errors import ApplicationError
from contour.tenancy.domain.access import Principal


class UnauthenticatedError(ApplicationError):
    """Signal that HTTP delivery could not verify a bearer credential."""

    def __init__(self) -> None:
        """Create a credential-safe authentication outcome."""
        super().__init__(code="auth.unauthenticated", message="Authentication is required.")


class CredentialVerifier(Protocol):
    """Verifies an HTTP bearer credential without exposing credential material."""

    def verify(self, credential: str) -> Principal | None:
        """Return the verified principal, or ``None`` for an invalid credential."""


def bearer_principal(verifier: CredentialVerifier) -> Callable[[str | None], Principal]:
    """Create the HTTP dependency that safely verifies one bearer credential."""

    def authenticate(authorization: str | None = Header(default=None)) -> Principal:
        """Return a verified principal or fail with the stable delivery error."""
        if authorization is None or not authorization.startswith("Bearer "):
            raise UnauthenticatedError()
        principal = verifier.verify(authorization.removeprefix("Bearer "))
        if principal is None:
            raise UnauthenticatedError()
        return principal

    return authenticate
