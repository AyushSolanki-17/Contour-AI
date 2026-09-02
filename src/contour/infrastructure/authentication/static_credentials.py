"""Configured opaque-credential adapter for local and demonstration deployments."""

from __future__ import annotations

from contour.tenancy.domain.access import Principal


class StaticCredentialVerifier:
    """Resolve explicitly configured opaque credentials to verified principals."""

    def __init__(self, credentials: dict[str, Principal]) -> None:
        """Copy the configured credential mapping into process-local adapter state."""
        self._credentials = credentials.copy()

    def verify(self, credential: str) -> Principal | None:
        """Return the configured principal for one exact opaque credential."""
        return self._credentials.get(credential)
