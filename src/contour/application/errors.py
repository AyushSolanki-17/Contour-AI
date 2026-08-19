"""Stable application errors that delivery adapters can translate."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class ApplicationError(Exception):
    """A safe, stable error contract for Contour application boundaries."""

    code: str
    message: str

    def __str__(self) -> str:
        return self.message


class ConfigurationError(ApplicationError):
    """Raised when required runtime configuration is absent or invalid."""

    def __init__(self, message: str) -> None:
        super().__init__(code="configuration.invalid", message=message)


class DependencyUnavailableError(ApplicationError):
    """Raised when a required runtime dependency cannot satisfy a check."""

    def __init__(self) -> None:
        super().__init__(
            code="dependency.unavailable",
            message="A required dependency is unavailable.",
        )
