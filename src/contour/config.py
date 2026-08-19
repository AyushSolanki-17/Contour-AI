"""Validated runtime settings loaded only at the application's edge."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from urllib.parse import quote

from contour.application.errors import ConfigurationError

_REQUIRED_DATABASE_VARIABLES = (
    "CONTOUR_POSTGRES_DB",
    "CONTOUR_POSTGRES_USER",
    "CONTOUR_POSTGRES_PASSWORD",
    "CONTOUR_POSTGRES_PORT",
)


@dataclass(frozen=True)
class DatabaseSettings:
    """PostgreSQL connection settings with secret-safe representation."""

    database: str
    username: str
    password: str = field(repr=False)
    host: str
    port: int

    @property
    def dsn(self) -> str:
        """Build the encoded database DSN for infrastructure adapters.

        Returns:
            A PostgreSQL connection string containing the configured credentials.
        """
        username = quote(self.username, safe="")
        password = quote(self.password, safe="")
        database = quote(self.database, safe="")
        return f"postgresql://{username}:{password}@{self.host}:{self.port}/{database}"

    @property
    def redaction_values(self) -> tuple[str, ...]:
        """Return sensitive values that logging must redact.

        Returns:
            The raw password and complete DSN.
        """
        return (self.password, self.dsn)


@dataclass(frozen=True)
class Settings:
    """All runtime settings required by the Phase 0 application boundary."""

    database: DatabaseSettings

    @classmethod
    def from_environment(cls, environment: dict[str, str] | None = None) -> Settings:
        """Load and validate required configuration without implicit fallbacks.

        Args:
            environment: Optional environment mapping used instead of ``os.environ``.

        Returns:
            Validated runtime settings.

        Raises:
            ConfigurationError: If a required value is missing or invalid.
        """
        values = os.environ if environment is None else environment
        missing = [name for name in _REQUIRED_DATABASE_VARIABLES if not values.get(name)]
        if missing:
            names = ", ".join(missing)
            raise ConfigurationError(f"Missing required configuration: {names}.")

        port_value = values["CONTOUR_POSTGRES_PORT"]
        try:
            port = int(port_value)
        except ValueError as error:
            raise ConfigurationError("CONTOUR_POSTGRES_PORT must be an integer.") from error
        if not 1 <= port <= 65535:
            raise ConfigurationError("CONTOUR_POSTGRES_PORT must be between 1 and 65535.")

        host = values.get("CONTOUR_POSTGRES_HOST", "127.0.0.1")
        if not host or any(character.isspace() for character in host):
            raise ConfigurationError("CONTOUR_POSTGRES_HOST must be a non-empty host name.")

        return cls(
            database=DatabaseSettings(
                database=values["CONTOUR_POSTGRES_DB"],
                username=values["CONTOUR_POSTGRES_USER"],
                password=values["CONTOUR_POSTGRES_PASSWORD"],
                host=host,
                port=port,
            )
        )
