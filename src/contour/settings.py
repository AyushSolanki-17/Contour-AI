"""Validated runtime settings loaded only at the application's edge."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from urllib.parse import quote

_REQUIRED_DATABASE_VARIABLES = (
    "CONTOUR_POSTGRES_DB",
    "CONTOUR_POSTGRES_USER",
    "CONTOUR_POSTGRES_PASSWORD",
    "CONTOUR_POSTGRES_PORT",
)


class ConfigurationError(ValueError):
    """Raised when required process configuration is absent or invalid."""


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
    cursor_signing_secret: str = field(repr=False)
    demo_credentials: dict[str, str] = field(default_factory=dict, repr=False)

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

        cursor_signing_secret = values.get("CONTOUR_CURSOR_SIGNING_SECRET")
        if not cursor_signing_secret:
            raise ConfigurationError("CONTOUR_CURSOR_SIGNING_SECRET must be non-empty.")

        raw_credentials = values.get("CONTOUR_DEMO_CREDENTIALS", "{}")
        try:
            encoded_credentials = json.loads(raw_credentials)
        except json.JSONDecodeError as error:
            raise ConfigurationError("CONTOUR_DEMO_CREDENTIALS must be a JSON object.") from error
        if not isinstance(encoded_credentials, dict) or not all(
            isinstance(token, str) and isinstance(principal_id, str)
            for token, principal_id in encoded_credentials.items()
        ):
            raise ConfigurationError(
                "CONTOUR_DEMO_CREDENTIALS must map opaque tokens to principal IDs."
            )
        credentials: dict[str, str] = {}
        try:
            for token, serialized_id in encoded_credentials.items():
                namespace, value = serialized_id.rsplit(":", 1)
                if not namespace or not value:
                    raise ValueError("empty principal identifier part")
                credentials[token] = serialized_id
        except (TypeError, ValueError) as error:
            raise ConfigurationError(
                "CONTOUR_DEMO_CREDENTIALS contains an invalid principal ID."
            ) from error

        return cls(
            database=DatabaseSettings(
                database=values["CONTOUR_POSTGRES_DB"],
                username=values["CONTOUR_POSTGRES_USER"],
                password=values["CONTOUR_POSTGRES_PASSWORD"],
                host=host,
                port=port,
            ),
            cursor_signing_secret=cursor_signing_secret,
            demo_credentials=credentials,
        )
