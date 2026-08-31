"""Persistence contract for exact evidence locators."""

from __future__ import annotations

from typing import Protocol

from contour.domain.access import AccessContext
from contour.domain.evidence import EvidenceId, EvidenceLocator


class EvidenceRepository(Protocol):
    """Persists exact evidence locators bound to immutable source versions."""

    def get_evidence(
        self, access: AccessContext, evidence_id: EvidenceId
    ) -> EvidenceLocator | None:
        """Return an exact evidence locator by stable identity, if admitted."""

    def save_evidence(
        self, access: AccessContext, evidence_id: EvidenceId, locator: EvidenceLocator
    ) -> None:
        """Persist one evidence record bound to exactly one source version."""
