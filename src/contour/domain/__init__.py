"""Framework-independent values that preserve Contour's knowledge invariants.

The package is organized by reader-facing domain concepts: workspaces define
admission scope; sources and source versions preserve immutable origin content;
evidence points exactly into a version; entities and relationships express
evidence-backed knowledge; jobs and runs retain durable execution state; and
time represents a known instant or an explicit unknown.
"""

from contour.domain.acquired_content import AcquiredContent
from contour.domain.entity import Entity, EntityId
from contour.domain.evidence import EvidenceId, EvidenceLocator
from contour.domain.job import Job, JobId
from contour.domain.relationship import Relationship, RelationshipId
from contour.domain.run import Run, RunId
from contour.domain.source import Source, SourceId
from contour.domain.source_version import ContentDigest, SourceVersion, SourceVersionId
from contour.domain.time_point import TimePoint
from contour.domain.workspace import Workspace, WorkspaceId

__all__ = [
    "AcquiredContent",
    "ContentDigest",
    "Entity",
    "EntityId",
    "EvidenceId",
    "EvidenceLocator",
    "Job",
    "JobId",
    "Relationship",
    "RelationshipId",
    "Run",
    "RunId",
    "SourceId",
    "Source",
    "SourceVersion",
    "SourceVersionId",
    "TimePoint",
    "Workspace",
    "WorkspaceId",
]
