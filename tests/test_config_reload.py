from pathlib import Path
import importlib
import os
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

config_module = importlib.import_module("atticus.config")


def test_load_settings_refreshes_env(tmp_path, monkeypatch):
    # Prepare isolated temp repo
    env_path = tmp_path / ".env"
    env_path.write_text("OPENAI_API_KEY=first-key\n", encoding="utf-8")
    (tmp_path / "config.yaml").write_text("{}\n", encoding="utf-8")

    # Make sure no ambient OS key can override our .env
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    # Tell the app we want .env to win
    monkeypatch.setenv("ATTICUS_ENV_PRIORITY", "env")

    # Optional: if your loader supports a DOTENV_PATH override, pin it
    monkeypatch.setenv("DOTENV_PATH", str(env_path))

    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        # Reload module so it (re)reads env with our settings
        cfg = importlib.reload(config_module)
        cfg.reset_settings_cache()

        first = cfg.load_settings()
        assert first.openai_api_key == "first-key"

        # Update .env and ensure mtime changes
        time.sleep(1.1)
        env_path.write_text("OPENAI_API_KEY=second-key\n", encoding="utf-8")
        os.utime(env_path, None)

        # Either reset cache or reload to force re-read
        cfg.reset_settings_cache()
        second = cfg.load_settings()
        assert second.openai_api_key == "second-key"

    finally:
        os.chdir(old_cwd)
        importlib.reload(config_module)
        config_module.reset_settings_cache()


def test_evaluation_thresholds_property(monkeypatch):
    monkeypatch.setenv("EVAL_MIN_NDCG", "0.65")
    monkeypatch.setenv("EVAL_MIN_MRR", "0.6")

    config_module.reset_settings_cache()
    settings = config_module.load_settings()

    thresholds = settings.evaluation_thresholds
    assert thresholds["nDCG@10"] == 0.65
    assert thresholds["MRR"] == 0.6
