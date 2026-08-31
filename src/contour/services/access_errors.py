"""Safe application outcomes for tenant-scoped access enforcement."""

from __future__ import annotations

from contour.services.error import ApplicationError


class ResourceNotFoundError(ApplicationError):
    """Raised for unknown or inaccessible tenant-scoped resources."""

    def __init__(self) -> None:
        """Create one non-enumerating resource outcome."""
        super().__init__(code="resource.not_found", message="The requested resource was not found.")
