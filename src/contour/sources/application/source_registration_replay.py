"""Durable replay contract for source registration requests."""

from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
from json import dumps

from contour.sources.application.errors import IdempotencyConflictError
from contour.sources.application.idempotency_store import IdempotencyRepository
from contour.sources.domain.source import Source, SourceId
from contour.tenancy.domain.access import AccessContext
from contour.tenancy.domain.tenant import TenantId
from contour.workspaces.domain.workspace import WorkspaceId


class SourceRegistrationReplay:
    """Read and write the replay state for one source-registration request."""

    def __init__(
        self,
        *,
        access: AccessContext,
        workspace_id: WorkspaceId,
        key: str,
        payload: Mapping[str, str | None],
    ) -> None:
        """Define one replay namespace and its canonical request digest.

        Args:
            access: Verified tenant membership that owns the replay namespace.
            workspace_id: Workspace selected by the registration request.
            key: Client idempotency key for this request.
            payload: Source fields that determine replay equivalence.
        """
        self._access = access
        self._operation = f"sources:{workspace_id}"
        self._key = key
        self._digest = _payload_digest(payload)

    def read(self, repository: IdempotencyRepository) -> Source | None:
        """Return an equivalent prior source registration, if one exists.

        Args:
            repository: Idempotency records bound to the active transaction.

        Returns:
            Reconstructed source for a prior equivalent request, or ``None``.

        Raises:
            IdempotencyConflictError: If the key belongs to different source input.
        """
        replay = repository.get_result(
            self._access.principal,
            str(self._access.tenant_id),
            self._operation,
            self._key,
        )
        return None if replay is None else _source_from_replay(replay, self._digest)

    def save(self, repository: IdempotencyRepository, source: Source) -> None:
        """Persist the accepted source as the durable replay result.

        Args:
            repository: Idempotency records bound to the active transaction.
            source: Newly accepted source to reconstruct on a safe retry.
        """
        repository.save_result(
            self._access.principal,
            str(self._access.tenant_id),
            self._operation,
            self._key,
            self._digest,
            _source_result(source),
        )


def _payload_digest(payload: Mapping[str, str | None]) -> str:
    """Create a canonical source-request digest for replay comparison.

    Args:
        payload: Source fields that define replay equivalence.

    Returns:
        SHA-256 digest over canonical JSON input.
    """
    return sha256(dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _source_result(source: Source) -> dict[str, str | None]:
    """Serialize durable source fields needed to reconstruct a replay.

    Args:
        source: Newly accepted source.

    Returns:
        JSON-safe result stored beside the idempotency key.
    """
    return {
        "id": str(source.id),
        "tenant_id": str(source.tenant_id),
        "workspace_id": str(source.workspace_id),
        "connector_kind": source.source_type,
        "canonical_locator": source.canonical_locator,
        "scope": source.scope,
        "license": source.license,
        "data_classification": source.data_classification,
    }


def _source_from_replay(replay: tuple[str, dict[str, str | None]], digest: str) -> Source:
    """Validate and reconstruct a source from an idempotency record.

    Args:
        replay: Stored request digest and serialized source result.
        digest: Digest of the request currently being processed.

    Returns:
        Reconstructed source from the durable replay result.

    Raises:
        IdempotencyConflictError: If this key has different accepted input.
    """
    stored_digest, result = replay
    if stored_digest != digest:
        raise IdempotencyConflictError()
    return Source(
        _source_id(str(result["id"])),
        _tenant_id(str(result["tenant_id"])),
        _workspace_id(str(result["workspace_id"])),
        str(result["canonical_locator"]),
        str(result["connector_kind"]),
        str(result["scope"]),
        result["license"],
        str(result["data_classification"]),
    )


def _source_id(value: str) -> SourceId:
    """Rebuild a source identity from trusted internal replay data."""
    namespace, separator, local_value = value.rpartition(":")
    if not separator:
        raise ValueError("invalid stored identifier")
    return SourceId(namespace, local_value)


def _tenant_id(value: str) -> TenantId:
    """Rebuild a tenant identity from trusted internal replay data."""
    namespace, separator, local_value = value.rpartition(":")
    if not separator:
        raise ValueError("invalid stored identifier")
    return TenantId(namespace, local_value)


def _workspace_id(value: str) -> WorkspaceId:
    """Rebuild a workspace identity from trusted internal replay data."""
    namespace, separator, local_value = value.rpartition(":")
    if not separator:
        raise ValueError("invalid stored identifier")
    return WorkspaceId(namespace, local_value)
