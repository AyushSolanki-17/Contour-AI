"""Smoke tests for the project foundation."""

from contour import __version__


def test_package_exposes_its_version() -> None:
    assert __version__ == "0.0.1"
