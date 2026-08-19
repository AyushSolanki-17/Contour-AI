"""Reject oversized handwritten production Python modules."""

from __future__ import annotations

from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src" / "contour"
MAX_LINES = 600


def main() -> int:
    """Check production Python modules against the repository size limit."""
    oversized = [
        (path.relative_to(REPOSITORY_ROOT), len(path.read_text(encoding="utf-8").splitlines()))
        for path in sorted(SOURCE_ROOT.rglob("*.py"))
        if path.name != "__init__.py"
        and len(path.read_text(encoding="utf-8").splitlines()) > MAX_LINES
    ]
    if not oversized:
        return 0

    for path, line_count in oversized:
        print(f"{path}: {line_count} lines exceeds the {MAX_LINES}-line limit")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
