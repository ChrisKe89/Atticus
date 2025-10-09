import importlib
from typing import Any

import pytest


def _reload_logging_utils(monkeypatch: pytest.MonkeyPatch, **env: Any):
    for key in ("LOG_LEVEL", "LOG_FORMAT"):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, str(value))
    module = importlib.import_module("atticus.logging_utils")
    return importlib.reload(module)


def test_get_logger_json_format(monkeypatch: pytest.MonkeyPatch) -> None:
    logging_utils = _reload_logging_utils(monkeypatch, LOG_LEVEL="INFO", LOG_FORMAT="json")

    logger = logging_utils.get_logger("atticus-tests")
    assert hasattr(logger, "bind")
    logging_utils.get_logger("atticus-tests")
    assert getattr(logging_utils._configure_once, "_did", False)


def test_get_logger_console_format(monkeypatch: pytest.MonkeyPatch) -> None:
    logging_utils = _reload_logging_utils(monkeypatch, LOG_LEVEL="DEBUG", LOG_FORMAT="console")

    logger = logging_utils.get_logger("atticus-console")
    assert hasattr(logger, "bind")
    assert getattr(logging_utils._configure_once, "_did", False)
