"""Offline deterministic PEP source adapter for pinned fixtures."""

from __future__ import annotations

from dataclasses import dataclass

from contour.domain.source_version import ContentDigest
from contour.domain.time_point import TimePoint
from contour.infrastructure.source.pep import (
    PepAcquiredContent,
    PepFixtureUnavailableError,
    PepSourceConfiguration,
)


@dataclass(frozen=True, slots=True)
class PinnedPepFixture:
    """One integrity-declared public PEP fixture supplied to the adapter."""

    pep_number: int
    content: bytes
    content_digest: ContentDigest
    upstream_revision: str | None
    revision_time: TimePoint


class PepFixtureSourceAdapter:
    """Returns explicitly supplied PEP fixtures without network access."""

    def __init__(self, fixtures: tuple[PinnedPepFixture, ...]) -> None:
        """Initialize an immutable fixture mapping keyed by PEP number."""
        self._fixtures = {fixture.pep_number: fixture for fixture in fixtures}

    def acquire(self, configuration: PepSourceConfiguration) -> PepAcquiredContent:
        """Return the configured fixture or report that it is unavailable."""
        fixture = self._fixtures.get(configuration.pep_number)
        if fixture is None:
            raise PepFixtureUnavailableError()
        return PepAcquiredContent(
            fixture.content,
            fixture.content_digest,
            fixture.upstream_revision,
            fixture.revision_time,
        )
