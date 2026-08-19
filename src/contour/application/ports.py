"""Behavior-focused application ports for the first persistence slices."""

from __future__ import annotations

from typing import Protocol

from contour.domain import (
    Entity,
    EvidenceId,
    EvidenceLocator,
    Job,
    Relationship,
    Run,
    Source,
    SourceId,
    SourceVersion,
    Workspace,
    WorkspaceId,
)


class WorkspaceRepository(Protocol):
    """Reads and writes workspace records within an application transaction."""

    def get_workspace(self, workspace_id: WorkspaceId) -> Workspace | None:
        """Return one workspace by stable identity, if it exists."""

    def save_workspace(self, workspace: Workspace) -> None:
        """Persist a new workspace or reject a conflicting identity."""


class SourceRepository(Protocol):
    """Persists logical sources and immutable source-version evidence."""

    def get_source(self, source_id: SourceId) -> Source | None:
        """Return one logical source by stable identity, if it exists."""

    def save_source(self, source: Source) -> None:
        """Persist a new source or reject a conflicting identity."""

    def save_source_version(self, version: SourceVersion) -> None:
        """Persist one immutable source version without replacing prior content."""

    def save_evidence(self, evidence_id: EvidenceId, locator: EvidenceLocator) -> None:
        """Persist one evidence record bound to exactly one source version."""


class KnowledgeRepository(Protocol):
    """Persists evidence-backed entity and relationship assertions."""

    def save_entity(self, entity: Entity) -> None:
        """Persist one evidence-backed entity assertion."""

    def save_relationship(self, relationship: Relationship) -> None:
        """Persist one evidence-backed relationship assertion."""


class ExecutionRepository(Protocol):
    """Persists requested jobs and their distinct execution attempts."""

    def save_job(self, job: Job) -> None:
        """Persist one requested job and its lifecycle state."""

    def save_run(self, run: Run) -> None:
        """Persist one execution attempt linked to a requested job."""


class UnitOfWork(Protocol):
    """Defines the atomic application transaction boundary without SQL leakage."""

    workspaces: WorkspaceRepository
    sources: SourceRepository
    knowledge: KnowledgeRepository
    execution: ExecutionRepository

    def __enter__(self) -> UnitOfWork:
        """Begin or join the transaction and return its repository bundle."""

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        """Commit on success or roll back when the application raises."""


class TransactionManager(Protocol):
    """Creates an application-scoped unit of work for one use case."""

    def transaction(self) -> UnitOfWork:
        """Return a fresh transaction boundary for one application operation."""
