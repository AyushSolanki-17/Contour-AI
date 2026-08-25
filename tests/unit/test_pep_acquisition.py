"""Contracts for deterministic PEP source preflight and fixture acquisition."""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

import pytest

from contour.domain import ContentDigest, Source, SourceId, TimePoint, WorkspaceId
from contour.infrastructure.source.pep_fixture import PepFixtureSourceAdapter, PinnedPepFixture
from contour.services.pep_acquisition import (
    PepAcquiredContent,
    PepAcquisitionService,
    PepPreflightService,
    PepSourceIntegrityError,
    PepSourceMalformedContentError,
    PepSourceTimeoutError,
    PepSourceUnavailableError,
    PepSourceValidationError,
)

_FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "pep_0723.html"
_FIXTURE_DIGEST = "4e8af3f49e41dc047b7b5f583b324c6983b0730dfe8ec45e4d47c6ee0b2ebb5b"


class _TimeoutAcquirer:
    """Deterministic test adapter for a timed-out source operation."""

    def acquire(self, configuration: object) -> PepAcquiredContent:
        """Raise the timeout condition that the service must classify."""
        del configuration
        raise TimeoutError()


def _source(*, canonical_locator: str = "https://peps.python.org/pep-0723/") -> Source:
    """Create the one public PEP source admitted by this fixture."""
    return Source(
        SourceId("SOURCE:PEP", "723"),
        WorkspaceId("WORKSPACE", "test"),
        canonical_locator,
        "pep",
        "public",
        "PSF-2.0",
        "public",
    )


def _service(
    content: bytes | None = None, *, digest: str = _FIXTURE_DIGEST
) -> PepAcquisitionService:
    """Create the service over the deterministic PEP 723 fixture."""
    fixture_content = _FIXTURE_PATH.read_bytes() if content is None else content
    fixture = PinnedPepFixture(
        723,
        fixture_content,
        ContentDigest(digest),
        "pep-723-fixture-r1",
        TimePoint(datetime(2026, 8, 24, tzinfo=UTC)),
    )
    return PepAcquisitionService(PepPreflightService(), PepFixtureSourceAdapter((fixture,)))


def test_pinned_fixture_acquisition_is_deterministic_and_retains_revision_metadata() -> None:
    first = _service().acquire(_source())
    second = _service().acquire(_source())

    assert first == second
    assert first.content_digest.value == _FIXTURE_DIGEST
    assert first.upstream_revision == "pep-723-fixture-r1"
    assert first.revision_time.is_known


def test_preflight_rejects_invalid_configuration_before_fixture_lookup() -> None:
    with pytest.raises(PepSourceValidationError):
        _service().acquire(_source(canonical_locator="https://example.invalid/pep-0723/"))


@pytest.mark.parametrize(
    ("service", "error_type"),
    [
        (
            PepAcquisitionService(PepPreflightService(), PepFixtureSourceAdapter(())),
            PepSourceUnavailableError,
        ),
        (
            PepAcquisitionService(PepPreflightService(), _TimeoutAcquirer()),
            PepSourceTimeoutError,
        ),
        (
            _service(b"not a PEP document", digest=sha256(b"not a PEP document").hexdigest()),
            PepSourceMalformedContentError,
        ),
        (_service(digest="a" * 64), PepSourceIntegrityError),
    ],
)
def test_acquisition_classifies_failures_without_exposing_content(
    service: PepAcquisitionService, error_type: type[Exception]
) -> None:
    with pytest.raises(error_type) as error:
        service.acquire(_source())

    assert "PEP 723" not in str(error.value)
