"""CI guard: ensure __version__ matches pyproject.toml distribution version."""

from __future__ import annotations

from importlib.metadata import version

from spline_mcp import __version__


def test_version_sync() -> None:
    dist_version = version("spline-mcp")
    assert __version__ == dist_version, (
        f"__version__ ({__version__}) drifted from pyproject ({dist_version})"
    )
