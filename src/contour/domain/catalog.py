"""Framework-independent workspace and logical-source records."""

from __future__ import annotations

from dataclasses import dataclass

from contour.domain._validation import require_text
from contour.domain.identifiers import SourceId, WorkspaceId


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


@dataclass(frozen=True, slots=True)
class Source:
    """A stable logical origin without mutable latest content."""

    id: SourceId
    workspace_id: WorkspaceId
    canonical_locator: str
    source_type: str
    scope: str
    license: str | None
    data_classification: str

    def __post_init__(self) -> None:
        """Validate source ownership and explicit metadata values."""
        if not isinstance(self.id, SourceId):
            raise TypeError("id must be a SourceId")
        if not isinstance(self.workspace_id, WorkspaceId):
            raise TypeError("workspace_id must be a WorkspaceId")
        for field_name in ("canonical_locator", "source_type", "scope", "data_classification"):
            require_text(getattr(self, field_name), field_name=field_name)
        if self.license is not None:
            require_text(self.license, field_name="license")
