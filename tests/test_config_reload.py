import importlib
import os
import sys
import time
from contextlib import contextmanager
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import atticus.config as config_module


def test_load_settings_refreshes_env(tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text("OPENAI_API_KEY=first-key\n", encoding="utf-8")
    (tmp_path / "config.yaml").write_text("{}\n", encoding="utf-8")

    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        config = importlib.reload(config_module)
        config.reset_settings_cache()

        first = config.load_settings()
        assert first.openai_api_key == "first-key"
        assert first.secrets_report["OPENAI_API_KEY"]["resolved_source"] == ".env"

        time.sleep(1.1)
        env_path.write_text("OPENAI_API_KEY=second-key\n", encoding="utf-8")
        os.utime(env_path, None)

        second = config.load_settings()
        assert second.openai_api_key == "second-key"
        assert second.secrets_report["OPENAI_API_KEY"]["resolved_source"] == ".env"
    finally:
        os.chdir(old_cwd)
        importlib.reload(config_module)
        config_module.reset_settings_cache()


@contextmanager
def reload_for_env(tmp_path: Path):
    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        module = importlib.reload(config_module)
        module.reset_settings_cache()
        yield module
    finally:
        os.chdir(old_cwd)
        importlib.reload(config_module)
        config_module.reset_settings_cache()


def test_load_settings_prefers_env_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    env_path = tmp_path / ".env"
    env_path.write_text("OPENAI_API_KEY=file-key\n", encoding="utf-8")
    (tmp_path / "config.yaml").write_text("{}\n", encoding="utf-8")

    monkeypatch.setenv("OPENAI_API_KEY", "env-key")
    with reload_for_env(tmp_path) as module:
        settings = module.load_settings()

    assert settings.openai_api_key == "file-key"
    report = settings.secrets_report["OPENAI_API_KEY"]
    assert report["resolved_source"] == ".env"
    assert report["priority"] == "env"
    assert report["env_file_fingerprint"] == report["resolved_fingerprint"]
    assert report["conflict"] is True


def test_load_settings_priority_os(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    env_path = tmp_path / ".env"
    env_path.write_text("OPENAI_API_KEY=file-key\n", encoding="utf-8")
    (tmp_path / "config.yaml").write_text("{}\n", encoding="utf-8")

    monkeypatch.setenv("OPENAI_API_KEY", "env-key")
    monkeypatch.setenv("ATTICUS_ENV_PRIORITY", "os")
    with reload_for_env(tmp_path) as module:
        settings = module.load_settings()

    assert settings.openai_api_key == "env-key"
    report = settings.secrets_report["OPENAI_API_KEY"]
    assert report["resolved_source"] == "os.environ"
    assert report["priority"] == "os"
    assert report["conflict"] is True
