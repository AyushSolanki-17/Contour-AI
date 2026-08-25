"""Deterministic PEP source preflight and acquisition contracts."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Protocol

from contour.domain.source import Source, SourceId
from contour.domain.source_version import ContentDigest
from contour.domain.time_point import TimePoint
from contour.services.error import ApplicationError

_PEP_NAMESPACE = "SOURCE:PEP"
_PEP_SOURCE_TYPE = "pep"
_MAX_PEP_CONTENT_BYTES = 2 * 1024 * 1024


class PepSourceValidationError(ApplicationError):
    """Raised when a source is outside the supported PEP admission boundary."""

    def __init__(self) -> None:
        """Create a safe invalid-configuration error."""
        super().__init__(
            code="source.invalid_configuration",
            message="The source is not a supported public PEP configuration.",
        )


class PepSourceUnavailableError(ApplicationError):
    """Raised when a configured PEP source cannot currently be obtained."""

    def __init__(self) -> None:
        """Create a safe unavailable-source error."""
        super().__init__(
            code="source.unavailable",
            message="The configured PEP source is currently unavailable.",
        )


class PepSourceTimeoutError(ApplicationError):
    """Raised when acquisition exceeds its configured source-operation limit."""

    def __init__(self) -> None:
        """Create a safe timeout error."""
        super().__init__(code="source.timeout", message="PEP source acquisition timed out.")


class PepSourceMalformedContentError(ApplicationError):
    """Raised when acquired bytes are not a usable PEP document."""

    def __init__(self) -> None:
        """Create a safe malformed-content error without including source bytes."""
        super().__init__(
            code="source.malformed_content",
            message="The acquired PEP content is malformed or unsupported.",
        )


class PepSourceIntegrityError(ApplicationError):
    """Raised when acquired bytes do not match the fixture's declared digest."""

    def __init__(self) -> None:
        """Create a safe integrity error without including content or digests."""
        super().__init__(
            code="source.integrity_failed",
            message="The acquired PEP content failed its integrity check.",
        )


class PepFixtureUnavailableError(Exception):
    """Signals that a deterministic fixture does not contain the requested PEP."""


@dataclass(frozen=True, slots=True)
class PepSourceConfiguration:
    """Validated public PEP configuration accepted by the acquisition boundary."""

    source_id: SourceId
    pep_number: int
    canonical_locator: str


@dataclass(frozen=True, slots=True)
class PepAcquiredContent:
    """Provider-neutral bytes and metadata returned by one PEP source adapter."""

    content: bytes
    expected_digest: ContentDigest
    upstream_revision: str | None
    revision_time: TimePoint


@dataclass(frozen=True, slots=True)
class PepAcquisition:
    """Validated PEP bytes with stable content identity and upstream metadata."""

    configuration: PepSourceConfiguration
    content: bytes
    content_digest: ContentDigest
    upstream_revision: str | None
    revision_time: TimePoint


class PepContentAcquirer(Protocol):
    """Obtains bytes for a configuration that has already passed preflight."""

    def acquire(self, configuration: PepSourceConfiguration) -> PepAcquiredContent:
        """Return pinned PEP bytes or raise an adapter-specific availability error."""


class PepPreflightService:
    """Validates the one public PEP configuration supported in Phase 0."""

    def preflight(self, source: Source) -> PepSourceConfiguration:
        """Validate source metadata before any acquisition operation begins."""
        if source.source_type != _PEP_SOURCE_TYPE or source.id.namespace != _PEP_NAMESPACE:
            raise PepSourceValidationError()
        if source.scope != "public" or source.data_classification != "public":
            raise PepSourceValidationError()
        try:
            pep_number = int(source.id.value)
        except ValueError as error:
            raise PepSourceValidationError() from error
        if not 1 <= pep_number <= 9999 or source.id.value != str(pep_number):
            raise PepSourceValidationError()
        canonical_locator = f"https://peps.python.org/pep-{pep_number:04d}/"
        if source.canonical_locator != canonical_locator:
            raise PepSourceValidationError()
        return PepSourceConfiguration(source.id, pep_number, canonical_locator)


class PepAcquisitionService:
    """Acquires and validates deterministic PEP content through a narrow port."""

    def __init__(self, preflight: PepPreflightService, acquirer: PepContentAcquirer) -> None:
        """Initialize the service with explicit validation and source dependencies."""
        self._preflight = preflight
        self._acquirer = acquirer

    def acquire(self, source: Source) -> PepAcquisition:
        """Return validated, integrity-checked PEP content for a supported source.

        Raises:
            PepSourceValidationError: If source configuration is unsupported.
            PepSourceUnavailableError: If the adapter has no configured content.
            PepSourceTimeoutError: If the adapter times out.
            PepSourceMalformedContentError: If bytes are not an admitted PEP document.
            PepSourceIntegrityError: If bytes differ from the declared digest.
        """
        configuration = self._preflight.preflight(source)
        try:
            acquired = self._acquirer.acquire(configuration)
        except PepFixtureUnavailableError as error:
            raise PepSourceUnavailableError() from error
        except TimeoutError as error:
            raise PepSourceTimeoutError() from error

        content_digest = ContentDigest(sha256(acquired.content).hexdigest())
        if content_digest != acquired.expected_digest:
            raise PepSourceIntegrityError()
        _validate_pep_content(acquired.content, configuration.pep_number)
        return PepAcquisition(
            configuration,
            acquired.content,
            content_digest,
            acquired.upstream_revision,
            acquired.revision_time,
        )


def _validate_pep_content(content: bytes, pep_number: int) -> None:
    """Reject oversized, non-text, or non-PEP fixture content without exposing it."""
    if not content or len(content) > _MAX_PEP_CONTENT_BYTES:
        raise PepSourceMalformedContentError()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise PepSourceMalformedContentError() from error
    normalized = text.casefold()
    if "<html" not in normalized or f"pep {pep_number}" not in normalized:
        raise PepSourceMalformedContentError()
