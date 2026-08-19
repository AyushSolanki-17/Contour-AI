"""Health use cases independent of HTTP and database clients."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from contour.application.errors import DependencyUnavailableError


class ReadinessProbe(Protocol):
    """Checks whether a required service is currently usable."""

    def check(self) -> None:
        """Confirm the dependency can serve work.

        Raises:
            Exception: If the dependency is unavailable.
        """


@dataclass(frozen=True)
class HealthStatus:
    """A compact status payload suitable for transport translation."""

    status: Literal["live", "ready"]


class HealthService:
    """Provides distinct process liveness and dependency readiness checks."""

    def __init__(self, readiness_probe: ReadinessProbe) -> None:
        """Initialize health use cases with a dependency probe.

        Args:
            readiness_probe: Adapter that verifies required-service availability.
        """
        self._readiness_probe = readiness_probe

    def liveness(self) -> HealthStatus:
        """Report that the process can execute application code.

        Returns:
            The process liveness status without probing external services.
        """
        return HealthStatus(status="live")

    def readiness(self) -> HealthStatus:
        """Report whether required dependencies can serve application work.

        Returns:
            The ready status after the dependency probe succeeds.

        Raises:
            DependencyUnavailableError: If the dependency probe fails.
        """
        try:
            self._readiness_probe.check()
        except Exception as error:
            raise DependencyUnavailableError() from error
        return HealthStatus(status="ready")
