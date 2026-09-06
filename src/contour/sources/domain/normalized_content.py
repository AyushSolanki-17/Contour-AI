"""Source-neutral normalized content and exact raw-byte locator mappings."""

from __future__ import annotations

from dataclasses import dataclass

from contour.sources.domain.source_version import SourceVersionId


@dataclass(frozen=True, slots=True)
class NormalizedLocator:
    """Map one normalized field to an exact non-empty span in raw source bytes."""

    name: str
    raw_start: int
    raw_end: int

    def __post_init__(self) -> None:
        """Reject ambiguous locator names and byte spans."""
        if not isinstance(self.name, str) or not self.name or self.name.strip() != self.name:
            raise ValueError("name must be non-empty text without surrounding whitespace")
        if isinstance(self.raw_start, bool) or not isinstance(self.raw_start, int):
            raise TypeError("raw_start must be an integer")
        if isinstance(self.raw_end, bool) or not isinstance(self.raw_end, int):
            raise TypeError("raw_end must be an integer")
        if self.raw_start < 0 or self.raw_end <= self.raw_start:
            raise ValueError("raw locator spans must be non-negative and non-empty")

    def to_primitive(self) -> dict[str, str | int]:
        """Return a deterministic serialization for a normalized locator."""
        return {"name": self.name, "raw_start": self.raw_start, "raw_end": self.raw_end}


@dataclass(frozen=True, slots=True)
class NormalizedContent:
    """Deterministic normalized bytes derived from one immutable raw version."""

    source_version_id: SourceVersionId
    transformation: str
    content: bytes
    locators: tuple[NormalizedLocator, ...]

    def __post_init__(self) -> None:
        """Require source-qualified derivation, non-empty content, and unique fields."""
        if not isinstance(self.source_version_id, SourceVersionId):
            raise TypeError("source_version_id must be a SourceVersionId")
        if not isinstance(self.transformation, str) or not self.transformation:
            raise ValueError("transformation must be non-empty text")
        if not isinstance(self.content, bytes) or not self.content:
            raise ValueError("content must be non-empty bytes")
        if not all(isinstance(locator, NormalizedLocator) for locator in self.locators):
            raise TypeError("locators must contain only NormalizedLocator values")
        if len({locator.name for locator in self.locators}) != len(self.locators):
            raise ValueError("locator names must be unique")
