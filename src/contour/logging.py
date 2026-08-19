"""Minimal logging configuration with explicit secret redaction."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import Any


class SecretRedactionFilter(logging.Filter):
    """Replace configured secret values in log messages and arguments."""

    def __init__(self, secrets: Iterable[str]) -> None:
        """Initialize the filter with non-empty sensitive values.

        Args:
            secrets: Exact values to replace before a record is emitted.
        """
        super().__init__()
        self._secrets = tuple(secret for secret in secrets if secret)

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact a log record while allowing it to be emitted.

        Args:
            record: Mutable log record to sanitize.

        Returns:
            Always true so the sanitized record continues to its handler.
        """
        record.msg = self._redact(record.msg)
        record.args = self._redact(record.args)
        return True

    def _redact(self, value: Any) -> Any:
        """Recursively replace configured secrets in supported log values.

        Args:
            value: Message, arguments, or nested container to sanitize.

        Returns:
            A redacted value that preserves the supported container shape.
        """
        if isinstance(value, str):
            redacted = value
            for secret in self._secrets:
                redacted = redacted.replace(secret, "[REDACTED]")
            return redacted
        if isinstance(value, tuple):
            return tuple(self._redact(item) for item in value)
        if isinstance(value, dict):
            return {key: self._redact(item) for key, item in value.items()}
        return value


def configure_logging(*, secrets: Iterable[str]) -> None:
    """Configure Contour's logger without emitting settings or secrets.

    Args:
        secrets: Exact sensitive values to redact from log records.
    """
    handler = logging.StreamHandler()
    handler.addFilter(SecretRedactionFilter(secrets))
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logger = logging.getLogger("contour")
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
