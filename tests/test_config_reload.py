import importlib
import os
import sys
import time

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


        time.sleep(1.1)
        env_path.write_text("OPENAI_API_KEY=second-key\n", encoding="utf-8")
        os.utime(env_path, None)

        second = config.load_settings()
        assert second.openai_api_key == "second-key"

    finally:
        os.chdir(old_cwd)
        importlib.reload(config_module)
        config_module.reset_settings_cache()
