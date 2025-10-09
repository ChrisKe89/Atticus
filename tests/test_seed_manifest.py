"""Tests for the seed manifest generation workflow."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

config_module = pytest.importorskip("atticus.config")
utils_module = pytest.importorskip("atticus.utils")
chunker_module = pytest.importorskip("ingest.chunker")
parsers_module = pytest.importorskip("ingest.parsers")
seed_module = pytest.importorskip("scripts.make_seed")

load_settings = config_module.load_settings
reset_settings_cache = config_module.reset_settings_cache
sha256_file = utils_module.sha256_file
chunk_document = chunker_module.chunk_document
parse_document = parsers_module.parse_document
build_seed_manifest = seed_module.build_seed_manifest


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


def test_glossary_seed_entries_round_trip() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL must be set to verify glossary seeds.")

    if shutil.which("npm") is None:
        pytest.skip("npm is required to execute make db.seed")

    psycopg = pytest.importorskip("psycopg")

    env = os.environ.copy()
    env.setdefault("DEFAULT_ORG_ID", "org-atticus")
    env.setdefault("DEFAULT_ORG_NAME", "Atticus Default")
    env.setdefault("ADMIN_NAME", "Seed Admin")
    env.setdefault("ADMIN_EMAIL", "seed-admin@example.com")

    subprocess.run(["npm", "run", "db:seed"], check=True, env=env)

    expected = {
        "glossary-entry-managed-print-services": {
            "term": "Managed Print Services",
            "status": "APPROVED",
            "synonyms": ["MPS", "Print-as-a-service"],
            "requires_reviewer": True,
        },
        "glossary-entry-proactive-maintenance": {
            "term": "Proactive Maintenance",
            "status": "PENDING",
            "synonyms": ["Preventative maintenance"],
            "requires_reviewer": False,
        },
        "glossary-entry-toner-optimization": {
            "term": "Toner Optimization",
            "status": "REJECTED",
            "synonyms": ["Smart toner", "Consumable optimisation"],
            "requires_reviewer": True,
        },
    }

    with psycopg.connect(database_url) as connection:  # type: ignore[attr-defined]
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT "id", "term", "status", "synonyms", "authorId", "reviewerId", "reviewNotes", "reviewedAt" '
                'FROM "GlossaryEntry" WHERE "id" = ANY(%s)',
                (list(expected.keys()),),
            )
            rows = {
                row[0]: {
                    "term": row[1],
                    "status": row[2],
                    "synonyms": list(row[3] or ()),
                    "authorId": row[4],
                    "reviewerId": row[5],
                    "reviewNotes": row[6],
                    "reviewedAt": row[7],
                }
                for row in cursor.fetchall()
            }

    for entry_id, expectations in expected.items():
        assert entry_id in rows, f"Missing glossary seed {entry_id}"
        record = rows[entry_id]
        assert record["term"] == expectations["term"]
        assert record["status"] == expectations["status"]
        assert record["synonyms"] == expectations["synonyms"]
        assert record["authorId"], "Seed glossary entries must have an author"

        if expectations["requires_reviewer"]:
            assert record["reviewerId"], "Reviewer metadata should be present"
            assert record["reviewNotes"], "Reviewer notes should be populated"
            assert record["reviewedAt"], "Reviewed timestamp should be stored"
        else:
            assert record["reviewerId"] is None
            assert record["reviewNotes"] in (None, "")
