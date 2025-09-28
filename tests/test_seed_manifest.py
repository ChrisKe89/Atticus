"""Tests for the seed manifest generation workflow."""

from __future__ import annotations

from pathlib import Path

import pytest

from atticus.config import load_settings, reset_settings_cache
from atticus.utils import sha256_file
from ingest.chunker import chunk_document
from ingest.parsers import parse_document
from scripts.make_seed import build_seed_manifest


@pytest.fixture(autouse=True)
def _reset_settings():
    try:
        yield
    finally:
        reset_settings_cache()


def test_build_seed_manifest_includes_chunk_metadata(tmp_path, monkeypatch):
    content_dir = tmp_path / "content"
    content_dir.mkdir()

    document_path = content_dir / "sample.txt"
    document_path.write_text(
        "Heading\n" * 2
        + "Atticus seeds capture deterministic chunk metadata for CI verification." * 3,
        encoding="utf-8",
    )

    monkeypatch.setenv("CONTENT_ROOT", str(content_dir))
    indices_dir = tmp_path / "indices"
    monkeypatch.setenv("INDICES_DIR", str(indices_dir))
    monkeypatch.setenv("SNAPSHOTS_DIR", str(indices_dir / "snapshots"))
    monkeypatch.setenv("LOG_PATH", str(tmp_path / "logs" / "app.jsonl"))
    monkeypatch.setenv("ERROR_LOG_PATH", str(tmp_path / "logs" / "errors.jsonl"))
    monkeypatch.setenv("EVALUATION_RUNS_DIR", str(tmp_path / "eval_runs"))

    manifest = build_seed_manifest()
    assert len(manifest) == 1

    entry = manifest[0]
    assert entry["document"].endswith("sample.txt")
    assert entry["sha256"] == sha256_file(document_path)

    chunk_count = entry["chunk_count"]
    assert isinstance(chunk_count, int) and chunk_count > 0

    chunks = entry["chunks"]
    assert isinstance(chunks, list) and chunks
    assert chunk_count >= len(chunks)

    hashes = {chunk["sha256"] for chunk in chunks}
    assert len(hashes) == len(chunks)

    # Cross-check against the chunker directly for metadata consistency.
    settings = load_settings()
    parsed = parse_document(Path(entry["document"]))
    parsed.sha256 = entry["sha256"]
    actual_chunks = chunk_document(parsed, settings)
    assert chunk_count == len(actual_chunks)

    for chunk in chunks:
        assert chunk["chunk_id"]
        assert chunk["chunking"] in {"prose", "table", "footnote"}
        assert chunk["sha256"]
