import os

import pytest

from core import config


@pytest.fixture(autouse=True)
def _reset_settings():
    try:
        yield
    finally:
        config.reset_settings_cache()
        for key in ("EMBED_MODEL", "EMBED_DIMENSIONS", "PGVECTOR_PROBES", "PGVECTOR_LISTS"):
            os.environ.pop(key, None)


def test_embed_dimensions_must_match_model(monkeypatch):
    monkeypatch.setenv("EMBED_MODEL", "text-embedding-3-large")
    monkeypatch.setenv("EMBED_DIMENSIONS", "1536")
    with pytest.raises(ValueError, match="does not match the expected dimension"):
        config.load_settings()


def test_pgvector_probes_within_range(monkeypatch):
    monkeypatch.setenv("PGVECTOR_PROBES", "0")
    with pytest.raises(ValueError, match="pgvector_probes must be >= 1"):
        config.load_settings()


def test_pgvector_probes_not_exceed_lists(monkeypatch):
    monkeypatch.setenv("PGVECTOR_PROBES", "16")
    monkeypatch.setenv("PGVECTOR_LISTS", "8")
    with pytest.raises(ValueError, match="cannot exceed pgvector_lists"):
        config.load_settings()
