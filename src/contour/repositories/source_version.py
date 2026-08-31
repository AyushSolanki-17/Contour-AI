"""Persistence contract for immutable source-version records."""

from __future__ import annotations

from typing import Protocol

from contour.domain.access import AccessContext
from contour.domain.source_version import SourceVersion, SourceVersionId


class SourceVersionRepository(Protocol):
    """Persists immutable content-version records for logical sources."""

    def get_source_version(
        self, access: AccessContext, version_id: SourceVersionId
    ) -> SourceVersion | None:
        """Return one immutable source version by content identity, if it exists."""

    def save_source_version(self, access: AccessContext, version: SourceVersion) -> None:
        """Persist one immutable source version without replacing prior content."""
