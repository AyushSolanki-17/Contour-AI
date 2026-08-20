"""Workspace aggregate and identity for Contour's admission boundary.

A workspace is the isolated scope that owns sources and the knowledge derived
from them. Its identifier is defined beside the aggregate because neither has a
useful meaning independently of the other.
"""

from __future__ import annotations

from dataclasses import dataclass

from contour.domain.identifier_validation import require_identifier_value, require_namespace
from contour.domain.validation import require_text


@dataclass(frozen=True, slots=True)
class WorkspaceId:
    """A stable identifier for one isolated Contour workspace."""

    namespace: str
    value: str

    def __post_init__(self) -> None:
        """Reject malformed workspace identity components."""
        object.__setattr__(self, "namespace", require_namespace(self.namespace))
        object.__setattr__(self, "value", require_identifier_value(self.value, field_name="value"))

    def __str__(self) -> str:
        """Return the stable serialized workspace identifier."""
        return f"{self.namespace}:{self.value}"


@dataclass(frozen=True, slots=True)
class Workspace:
    """The isolated scope in which sources and derived knowledge are admitted."""

    id: WorkspaceId
    name: str
    owner: str
    settings: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        """Validate workspace identity and stable configuration values."""
        if not isinstance(self.id, WorkspaceId):
            raise TypeError("id must be a WorkspaceId")
        require_text(self.name, field_name="name")
        require_text(self.owner, field_name="owner")
        if not isinstance(self.settings, tuple):
            raise TypeError("settings must be a tuple of key/value pairs")
        for key, value in self.settings:
            require_text(key, field_name="settings key")
            require_text(value, field_name="settings value")
