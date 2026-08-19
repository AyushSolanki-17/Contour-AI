"""Health use cases independent of HTTP and database clients."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from contour.application.errors import DependencyUnavailableError


class ReadinessProbe(Protocol):
    """Checks whether a required service is currently usable."""

    def check(self) -> None:
        """Raise an exception when the service is unavailable."""


@dataclass(frozen=True)
class HealthStatus:
    """A compact status payload suitable for transport translation."""

    status: str


class HealthService:
    """Provides distinct process liveness and dependency readiness checks."""

    def __init__(self, readiness_probe: ReadinessProbe) -> None:
        self._readiness_probe = readiness_probe

    def liveness(self) -> HealthStatus:
        return HealthStatus(status="live")

    def readiness(self) -> HealthStatus:
        try:
            self._readiness_probe.check()
        except Exception as error:
            raise DependencyUnavailableError() from error
        return HealthStatus(status="ready")
