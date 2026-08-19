"""Tests for secret redaction in structured logging inputs."""

from __future__ import annotations

import logging

from contour.logging import SecretRedactionFilter


def test_secret_redaction_filter_removes_secret_from_message_and_arguments() -> None:
    secret = "not-for-logs"
    record = logging.LogRecord(
        name="contour.test",
        level=logging.ERROR,
        pathname=__file__,
        lineno=1,
        msg="Failed to connect using %s",
        args=(secret,),
        exc_info=None,
    )

    SecretRedactionFilter([secret]).filter(record)

    assert secret not in record.getMessage()
    assert "[REDACTED]" in record.getMessage()
