"""Contract tests for repository quality checks."""

import runpy
from pathlib import Path

ROOT = Path(__file__).parent.parent
DOCS_CHECK = runpy.run_path(str(ROOT / "scripts/check_docs_links.py"))


def test_docs_link_checker_reports_missing_local_target(tmp_path: Path) -> None:
    document = tmp_path / "README.md"
    document.write_text("[missing](absent.md)\n", encoding="utf-8")

    assert DOCS_CHECK["invalid_links"](document) == [
        f"{document}: missing local link target 'absent.md'"
    ]
