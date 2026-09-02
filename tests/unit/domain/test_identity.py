"""Contracts for Phase 0 source identity and exact-evidence values."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone

import pytest

from contour.knowledge.domain.evidence import EvidenceId, EvidenceLocator
from contour.sources.domain.source import SourceId
from contour.sources.domain.source_version import ContentDigest, SourceVersion, SourceVersionId
from contour.tenancy.domain.tenant import TenantId
from contour.time import TimePoint
from contour.workspaces.domain.workspace import WorkspaceId


def source_id() -> SourceId:
    return SourceId(namespace="SOURCE:PEP", value="723")


def digest() -> ContentDigest:
    return ContentDigest("a" * 64)


def version_id() -> SourceVersionId:
    return SourceVersionId(source_id=source_id(), content_digest=digest())


def tenant_id() -> TenantId:
    """Return a valid tenant identity for ownership-bound records."""
    return TenantId("TENANT", "test")


def workspace_id() -> WorkspaceId:
    """Return a valid workspace identity for ownership-bound records."""
    return WorkspaceId("WORKSPACE", "test")


def test_typed_identifiers_reject_malformed_and_mixed_values() -> None:
    with pytest.raises(ValueError, match="namespace"):
        SourceId(namespace="source:pep", value="723")
    with pytest.raises(ValueError, match="digest"):
        ContentDigest("not-a-digest")
    with pytest.raises(TypeError, match="SourceId"):
        SourceVersionId(source_id=EvidenceId("EVIDENCE", "e-1"), content_digest=digest())  # type: ignore[arg-type]


def test_source_version_identity_is_immutable_and_serializable() -> None:
    identity = version_id()
    source_version = SourceVersion(
        id=identity,
        tenant_id=tenant_id(),
        workspace_id=workspace_id(),
        source_id=source_id(),
        content_digest=digest(),
        observed_at=TimePoint(datetime(2026, 8, 20, 13, 0, tzinfo=UTC)),
        upstream_revision="pep-723-2026-08-19",
        source_time=TimePoint.unknown(),
        revision_time=TimePoint(datetime(2026, 8, 19, 10, 30, tzinfo=UTC)),
    )

    with pytest.raises(FrozenInstanceError):
        source_version.upstream_revision = "another-revision"  # type: ignore[misc]

    assert source_version.to_primitive() == {
        "id": "SOURCE:PEP:723@sha256:" + "a" * 64,
        "tenant_id": "TENANT:test",
        "workspace_id": "WORKSPACE:test",
        "source_id": "SOURCE:PEP:723",
        "content_digest": "sha256:" + "a" * 64,
        "observed_at": "2026-08-20T13:00:00Z",
        "upstream_revision": "pep-723-2026-08-19",
        "source_time": None,
        "revision_time": "2026-08-19T10:30:00Z",
    }


def test_source_version_rejects_identity_for_other_content() -> None:
    with pytest.raises(ValueError, match="content_digest"):
        SourceVersion(
            id=version_id(),
            tenant_id=tenant_id(),
            workspace_id=workspace_id(),
            source_id=source_id(),
            content_digest=ContentDigest("b" * 64),
            observed_at=TimePoint(datetime(2026, 8, 20, 13, 0, tzinfo=UTC)),
            upstream_revision=None,
            source_time=TimePoint.unknown(),
            revision_time=TimePoint.unknown(),
        )


def test_evidence_locator_is_bound_to_one_version_and_exact_span() -> None:
    locator = EvidenceLocator(
        tenant_id=tenant_id(),
        workspace_id=workspace_id(),
        source_version_id=version_id(),
        locator="header:Replaces",
        start_offset=10,
        end_offset=23,
    )

    assert locator.to_primitive() == {
        "tenant_id": "TENANT:test",
        "workspace_id": "WORKSPACE:test",
        "source_version_id": "SOURCE:PEP:723@sha256:" + "a" * 64,
        "locator": "header:Replaces",
        "start_offset": 10,
        "end_offset": 23,
    }
    with pytest.raises(ValueError, match="both start_offset"):
        EvidenceLocator(
            tenant_id=tenant_id(),
            workspace_id=workspace_id(),
            source_version_id=version_id(),
            locator="header:Replaces",
            start_offset=10,
        )
    with pytest.raises(ValueError, match="positive length"):
        EvidenceLocator(
            tenant_id=tenant_id(),
            workspace_id=workspace_id(),
            source_version_id=version_id(),
            locator="header:Replaces",
            start_offset=23,
            end_offset=23,
        )


def test_unknown_time_stays_distinct_from_a_known_timezone_normalized_instant() -> None:
    unknown = TimePoint.unknown()
    known = TimePoint(datetime(2026, 8, 19, 16, 0, tzinfo=timezone(timedelta(hours=5, minutes=30))))

    assert not unknown.is_known
    assert unknown.to_primitive() is None
    assert known.is_known
    assert known.to_primitive() == "2026-08-19T10:30:00Z"
