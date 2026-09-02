"""Transport-neutral error contract for application boundaries."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class ApplicationError(Exception):
    """A safe, stable error contract for Contour application boundaries."""

    code: str
    message: str

    def __str__(self) -> str:
        """Return the safe application-facing error message."""
        return self.message
