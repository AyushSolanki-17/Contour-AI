"""Transaction contract for atomic evidence-backed knowledge admission."""

from __future__ import annotations

from types import TracebackType
from typing import Protocol, Self

from contour.repositories.entity import EntityRepository
from contour.repositories.relationship import RelationshipRepository


class KnowledgeUnitOfWork(Protocol):
    """Provide knowledge repositories bound to one atomic operation."""

    @property
    def entities(self) -> EntityRepository:
        """Return the entity repository bound to this transaction."""

    @property
    def relationships(self) -> RelationshipRepository:
        """Return the relationship repository bound to this transaction."""

    def __enter__(self) -> Self:
        """Begin the transaction and return its repositories."""

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Commit on success or discard all knowledge writes on failure."""


class KnowledgeTransactionManager(Protocol):
    """Create one explicit atomic boundary for knowledge admission."""

    def transaction(self) -> KnowledgeUnitOfWork:
        """Return a fresh knowledge transaction."""
