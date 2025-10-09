"""Ensure API metadata stays aligned with the repository VERSION file."""

from __future__ import annotations

from pathlib import Path

from api.main import app


def test_api_version_matches_repo_version() -> None:
    version_path = Path(__file__).resolve().parents[1] / "VERSION"
    expected = version_path.read_text(encoding="utf-8").strip()
    assert app.version == expected
