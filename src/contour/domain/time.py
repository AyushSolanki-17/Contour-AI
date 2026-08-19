"""Framework-independent temporal values that preserve an explicit unknown."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class TimePoint:
    """A known UTC instant or an explicit unknown temporal value."""

    value: datetime | None

    def __post_init__(self) -> None:
        """Require known instants to carry timezone information."""
        if self.value is not None and not isinstance(self.value, datetime):
            raise TypeError("time value must be a datetime or None")
        if self.value is not None and self.value.tzinfo is None:
            raise ValueError("known time values must include a timezone")
        if self.value is not None:
            object.__setattr__(self, "value", self.value.astimezone(UTC))

    @classmethod
    def unknown(cls) -> TimePoint:
        """Create an explicit unknown temporal value."""
        return cls(None)

    @property
    def is_known(self) -> bool:
        """Report whether this value contains a real instant."""
        return self.value is not None

    def to_primitive(self) -> str | None:
        """Serialize the instant without converting an unknown into a timestamp."""
        return self.value.isoformat().replace("+00:00", "Z") if self.value else None
