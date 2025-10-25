"""Tests for environment diagnostics helper."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from atticus import config as config_module


@pytest.fixture(autouse=True)
def reset_settings_cache():
    config_module.reset_settings_cache()
    yield
    config_module.reset_settings_cache()


def test_environment_diagnostics_reports_sources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        """
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/atticus
OPENAI_API_KEY=sk-debug
PGVECTOR_LISTS=256
""".strip()
        + "\n",
        encoding="utf-8",
    )

    config_path = tmp_path / "config.yaml"
    config_path.write_text("pgvector_lists: 128\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("PGVECTOR_LISTS", raising=False)
    monkeypatch.setenv("SMTP_USER", "smtp-user")

    diagnostics = config_module.environment_diagnostics()

    assert diagnostics["env_file"]["path"] == str(env_file)
    assert diagnostics["env_file"]["exists"] is True
    assert diagnostics["config_file"]["path"] == str(config_path)
    assert diagnostics["config_file"]["exists"] is True

    secrets = diagnostics["secrets"]
    db_secret = secrets["database_url"]
    assert db_secret["source"] == ".env:DATABASE_URL"
    expected_fp = hashlib.sha256(
        b"postgresql://postgres:postgres@localhost:5432/atticus"
    ).hexdigest()[:12]
    assert db_secret["fingerprint"] == expected_fp
    assert secrets["openai_api_key"]["source"] == ".env:OPENAI_API_KEY"
    assert secrets["smtp_user"]["source"] == "os.environ:SMTP_USER"
    assert secrets["smtp_user"]["defined"] is True

    settings_snapshot = diagnostics["settings"]
    assert settings_snapshot["pgvector_lists"]["value"] == 256
    assert settings_snapshot["pgvector_lists"]["source"] == ".env:PGVECTOR_LISTS"

    # Ensure secrets are excluded from the public settings snapshot.
    assert "database_url" not in settings_snapshot
    assert "openai_api_key" not in settings_snapshot

    overrides = diagnostics["overrides"]
    assert "SMTP_USER" in overrides["environment"]
    assert "DATABASE_URL" in overrides[".env"]
