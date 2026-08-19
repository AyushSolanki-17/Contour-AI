"""Validate local Markdown links in repository documentation."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

LINK_PATTERN = re.compile(r"(?<!!)\[[^]]*]\(([^)\s]+)(?:\s+[^)]*)?\)")


def markdown_files(paths: list[Path]) -> list[Path]:
    """Collect Markdown files from explicit files and recursive directories.

    Args:
        paths: Files or directories to inspect.

    Returns:
        Markdown file paths found in the supplied locations.
    """
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            files.extend(path.rglob("*.md"))
        elif path.suffix == ".md":
            files.append(path)
    return files


def invalid_links(path: Path) -> list[str]:
    """Find local Markdown link targets that do not exist.

    Args:
        path: Markdown document to inspect.

    Returns:
        Human-readable errors for missing local targets.
    """
    errors: list[str] = []
    for target in LINK_PATTERN.findall(path.read_text(encoding="utf-8")):
        location = target.split("#", maxsplit=1)[0]
        if not location or "://" in location or location.startswith("mailto:"):
            continue
        resolved = (path.parent / unquote(location)).resolve()
        if not resolved.exists():
            errors.append(f"{path}: missing local link target {target!r}")
    return errors


def main() -> int:
    """Run repository Markdown-link validation.

    Returns:
        Zero when all local targets exist; otherwise one.
    """
    paths = [Path(argument) for argument in sys.argv[1:]] or [Path("README.md"), Path("docs")]
    errors = [error for path in markdown_files(paths) for error in invalid_links(path)]
    if errors:
        print("\n".join(sorted(errors)), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
