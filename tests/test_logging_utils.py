import importlib
import sys

import pytest

from core.config import AppSettings


def _reload_logging_utils(monkeypatch: pytest.MonkeyPatch, *, log_level: str, log_format: str):
    sys.modules.pop("atticus.logging_utils", None)
    module = importlib.import_module("atticus.logging_utils")
    settings = AppSettings(log_level=log_level, log_format=log_format)
    monkeypatch.setattr(module, "load_settings", lambda: settings)
    return module


def test_get_logger_json_format(monkeypatch: pytest.MonkeyPatch) -> None:
    logging_utils = _reload_logging_utils(monkeypatch, log_level="INFO", log_format="json")

    logger = logging_utils.get_logger("atticus-tests")
    assert hasattr(logger, "bind")
    logging_utils.get_logger("atticus-tests")
    assert getattr(logging_utils._configure_once, "_did", False)


def test_get_logger_console_format(monkeypatch: pytest.MonkeyPatch) -> None:
    logging_utils = _reload_logging_utils(monkeypatch, log_level="DEBUG", log_format="console")

    logger = logging_utils.get_logger("atticus-console")
    assert hasattr(logger, "bind")
    assert getattr(logging_utils._configure_once, "_did", False)
