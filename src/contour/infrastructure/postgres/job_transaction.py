"""PostgreSQL transaction composition for jobs and execution attempts."""

from __future__ import annotations

from types import TracebackType

from sqlalchemy import Engine

from contour.infrastructure.postgres.job_repository import PostgresJobRepository
from contour.infrastructure.postgres.run_repository import PostgresRunRepository
from contour.infrastructure.postgres.transaction_scope import PostgresTransactionScope
from contour.jobs.application.job_store import JobRepository
from contour.jobs.application.run_store import RunRepository


class PostgresJobTransactionManager:
    """Create PostgreSQL transactions for one job-recording operation."""

    def __init__(self, engine: Engine) -> None:
        """Initialize the manager with an engine owned by composition.

        Args:
            engine: SQLAlchemy engine that owns the connection pool.
        """
        self._engine = engine

    def transaction(self) -> PostgresJobUnitOfWork:
        """Create an unopened job-scoped unit of work.

        Returns:
            A transaction that exposes only job and run repositories.
        """
        return PostgresJobUnitOfWork(self._engine)


class PostgresJobUnitOfWork:
    """Bind job and run repositories to one atomic transaction."""

    def __init__(self, engine: Engine) -> None:
        """Initialize an unopened job transaction.

        Args:
            engine: SQLAlchemy engine that owns the connection pool.
        """
        self._scope = PostgresTransactionScope(engine)
        self._jobs: JobRepository | None = None
        self._runs: RunRepository | None = None

    @property
    def jobs(self) -> JobRepository:
        """Return the job repository in the active transaction.

        Returns:
            Job repository bound to this transaction.

        Raises:
            RuntimeError: If the transaction has not been opened.
        """
        return self._require_active(self._jobs, name="job repository")

    @property
    def runs(self) -> RunRepository:
        """Return the run repository in the active transaction.

        Returns:
            Run repository bound to this transaction.

        Raises:
            RuntimeError: If the transaction has not been opened.
        """
        return self._require_active(self._runs, name="run repository")

    def __enter__(self) -> PostgresJobUnitOfWork:
        """Open the transaction and compose its job repositories.

        Returns:
            This active unit of work.
        """
        connection = self._scope.open()
        self._jobs = PostgresJobRepository(connection)
        self._runs = PostgresRunRepository(connection)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Complete the transaction and remove scoped repository references."""
        self._clear()
        self._scope.close(exc_type, exc_value, traceback)

    def _clear(self) -> None:
        """Release repositories that are valid only while the scope is open."""
        self._jobs = None
        self._runs = None

    @staticmethod
    def _require_active[T](resource: T | None, *, name: str) -> T:
        """Return an active repository or reject out-of-scope use.

        Args:
            resource: Repository initialized when the transaction began.
            name: Human-readable repository name for the error message.

        Returns:
            The initialized repository.

        Raises:
            RuntimeError: If the transaction scope is not active.
        """
        if resource is None:
            raise RuntimeError(f"job {name} requires an active transaction")
        return resource
