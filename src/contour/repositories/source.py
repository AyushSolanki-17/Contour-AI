"""Persistence contract for logical source records."""

from __future__ import annotations

from typing import Protocol

from contour.domain.source import Source, SourceId


class SourceRepository(Protocol):
    """Persists logical source records within an application transaction."""

    def get_source(self, source_id: SourceId) -> Source | None:
        """Return one logical source by stable identity, if it exists."""

    def save_source(self, source: Source) -> None:
        """Persist a new source or reject a conflicting identity."""
