"""Provider-neutral bearer credential verification boundary."""

from __future__ import annotations

from typing import Protocol

from contour.domain.access import Principal


class CredentialVerifier(Protocol):
    """Verifies a bearer credential without exposing credential material."""

    def verify(self, credential: str) -> Principal | None:
        """Return the verified principal, or ``None`` for an invalid credential."""


class StaticCredentialVerifier:
    """Local/demo credential adapter backed by explicitly configured opaque tokens."""

    def __init__(self, credentials: dict[str, Principal]) -> None:
        """Bind the adapter to a process-local token-to-principal mapping."""
        self._credentials = credentials.copy()

    def verify(self, credential: str) -> Principal | None:
        """Return the configured principal for one exact opaque credential."""
        return self._credentials.get(credential)
