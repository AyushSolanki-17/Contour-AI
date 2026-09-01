"""Signed opaque cursors for the public authenticated collection contract."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from collections.abc import Mapping
from dataclasses import dataclass

from contour.services.resource_errors import ResourceNotFoundError


@dataclass(frozen=True, slots=True)
class CursorScope:
    """The immutable identity and query shape to which one cursor is bound."""

    principal_id: str
    tenant_id: str
    route: str
    query: dict[str, str]


class CursorCodec:
    """Signs and verifies route-bound opaque continuation cursors."""

    def __init__(self, secret: str) -> None:
        """Bind the codec to an application-secret signing key.

        Raises:
            ValueError: If the supplied signing key is empty.
        """
        if not secret:
            raise ValueError("cursor secret must not be empty")
        self._secret = secret.encode("utf-8")

    def encode(self, scope: CursorScope, after: str) -> str:
        """Return an opaque token bound to the scope and last returned identity."""
        payload = {
            "p": scope.principal_id,
            "t": scope.tenant_id,
            "r": scope.route,
            "q": scope.query,
            "a": after,
        }
        encoded = _encode(payload)
        signature = hmac.new(self._secret, encoded, hashlib.sha256).digest()
        return f"{_base64(encoded)}.{_base64(signature)}"

    def decode(self, token: str, scope: CursorScope) -> str:
        """Return the continuation identity only when the token matches its scope.

        Raises:
            ResourceNotFoundError: If the token is malformed, forged, or out of scope.
        """
        try:
            encoded_part, signature_part = token.split(".", 1)
            encoded = _unbase64(encoded_part)
            supplied_signature = _unbase64(signature_part)
            expected_signature = hmac.new(self._secret, encoded, hashlib.sha256).digest()
            payload = json.loads(encoded)
            if not hmac.compare_digest(supplied_signature, expected_signature):
                raise ValueError("signature mismatch")
            if (
                not isinstance(payload, dict)
                or {
                    "p": scope.principal_id,
                    "t": scope.tenant_id,
                    "r": scope.route,
                    "q": scope.query,
                }.items()
                > payload.items()
            ):
                raise ValueError("scope mismatch")
            after = payload["a"]
            if not isinstance(after, str):
                raise ValueError("missing continuation")
            return after
        except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as error:
            raise ResourceNotFoundError() from error


def _encode(payload: Mapping[str, object]) -> bytes:
    """Encode a cursor payload canonically before signing it."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _base64(value: bytes) -> str:
    """Use unpadded URL-safe base64 for browser-safe opaque tokens."""
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _unbase64(value: str) -> bytes:
    """Decode an unpadded URL-safe base64 component."""
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
