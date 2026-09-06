"""Deterministic normalization for the bounded PEP HTML conformance fixture."""

from __future__ import annotations

from html.parser import HTMLParser

from contour.sources.domain.normalized_content import NormalizedContent, NormalizedLocator
from contour.sources.domain.source_version import SourceVersion


class PepNormalizationError(ValueError):
    """Raised when PEP HTML cannot preserve a required exact raw locator."""


class _PepTextParser(HTMLParser):
    """Extract the title and first paragraph from the supported fixture shape."""

    def __init__(self) -> None:
        """Initialize parser state for title and summary extraction."""
        super().__init__(convert_charrefs=True)
        self._tag: str | None = None
        self.title: str | None = None
        self.summary: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Track tags that supply normalization fields."""
        del attrs
        if tag in {"h1", "p"}:
            self._tag = tag

    def handle_endtag(self, tag: str) -> None:
        """Stop capturing text after a supported field closes."""
        if tag == self._tag:
            self._tag = None

    def handle_data(self, data: str) -> None:
        """Record the first non-empty title and summary field."""
        value = data.strip()
        if not value:
            return
        if self._tag == "h1" and self.title is None:
            self.title = value
        elif self._tag == "p" and self.summary is None:
            self.summary = value


class PepHtmlNormalizer:
    """Normalize supported PEP HTML while retaining exact raw-byte provenance."""

    transformation = "pep-html-normalizer-v1"

    def normalize(self, version: SourceVersion, raw_content: bytes) -> NormalizedContent:
        """Return canonical PEP fields and locators into the immutable raw bytes.

        Raises:
            PepNormalizationError: If HTML fields or their exact raw spans cannot be retained.
        """
        if version.source_id.namespace != "SOURCE:PEP":
            raise PepNormalizationError("unsupported source")
        try:
            text = raw_content.decode("utf-8")
        except UnicodeDecodeError as error:
            raise PepNormalizationError("invalid UTF-8") from error
        parser = _PepTextParser()
        try:
            parser.feed(text)
            parser.close()
        except ValueError as error:
            raise PepNormalizationError("malformed HTML") from error
        if parser.title is None or parser.summary is None:
            raise PepNormalizationError("required PEP fields are absent")
        title = _raw_locator(raw_content, parser.title, "header:title", "h1")
        summary = _raw_locator(raw_content, parser.summary, "content:summary", "p")
        content = f"title: {parser.title}\nsummary: {parser.summary}\n".encode()
        return NormalizedContent(version.id, self.transformation, content, (title, summary))


def _raw_locator(raw_content: bytes, value: str, name: str, tag: str) -> NormalizedLocator:
    """Locate a parsed field inside its expected raw HTML element or fail explicitly."""
    encoded = value.encode("utf-8")
    open_tag = raw_content.find(f"<{tag}".encode("ascii"))
    close_tag = raw_content.find(f"</{tag}>".encode("ascii"), open_tag)
    start = raw_content.find(encoded, open_tag, close_tag)
    if start < 0:
        raise PepNormalizationError("normalized value lost its raw locator")
    return NormalizedLocator(name, start, start + len(encoded))
