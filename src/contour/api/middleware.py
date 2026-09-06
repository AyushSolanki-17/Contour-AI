"""Small, transport-level middleware used by every HTTP request."""

from __future__ import annotations

from uuid import uuid4

from starlette.types import ASGIApp, Message, Receive, Scope, Send

_CORRELATION_HEADER = b"x-correlation-id"
_RESPONSE_CORRELATION_HEADER = (b"X-Correlation-ID",)


class RequestContextMiddleware:
    """Attach a bounded, non-secret correlation ID to request and response."""

    def __init__(self, app: ASGIApp) -> None:
        """Wrap an ASGI application with request context propagation."""
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Propagate a caller ID or create one without buffering the request."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        correlation_id = _request_correlation_id(scope)
        state = scope.setdefault("state", {})
        state["correlation_id"] = correlation_id

        async def send_with_context(message: Message) -> None:
            """Add the correlation header to the first response start message."""
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((_RESPONSE_CORRELATION_HEADER[0], correlation_id.encode("ascii")))
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_context)


def _request_correlation_id(scope: Scope) -> str:
    """Return a safe ASCII correlation ID from the request or generate one."""
    for name, value in scope.get("headers", []):
        if name == _CORRELATION_HEADER:
            try:
                candidate = bytes(value).decode("ascii")
            except UnicodeDecodeError:
                break
            if 1 <= len(candidate) <= 128 and all(32 <= ord(char) <= 126 for char in candidate):
                return candidate
            break
    return str(uuid4())
