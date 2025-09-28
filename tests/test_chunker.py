from pathlib import Path

import sys
import types

from atticus.config import AppSettings

psycopg_stub = types.ModuleType("psycopg")
psycopg_stub.rows = types.SimpleNamespace(dict_row=None)
psycopg_stub.types = types.SimpleNamespace(json=types.SimpleNamespace(Json=lambda value: value))
psycopg_stub.connect = lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("psycopg stubbed"))
sys.modules.setdefault("psycopg", psycopg_stub)

pgvector_stub = types.ModuleType("pgvector")
pgvector_psycopg_stub = types.ModuleType("pgvector.psycopg")

class _Vector(list):
    def __init__(self, values):
        super().__init__(values)


pgvector_psycopg_stub.register_vector = lambda conn: None
pgvector_psycopg_stub.Vector = _Vector
sys.modules.setdefault("pgvector", pgvector_stub)
sys.modules["pgvector.psycopg"] = pgvector_psycopg_stub

ingest_pkg = types.ModuleType("ingest")
ingest_pkg.__path__ = [str(Path("ingest"))]
sys.modules.setdefault("ingest", ingest_pkg)


from ingest.chunker import chunk_document
from ingest.models import ParsedDocument, ParsedSection


def test_ced_chunker_deduplicates_and_labels() -> None:
    settings = AppSettings()
    sections = [
        ParsedSection(text="Paragraph alpha beta.", heading="Intro"),
        ParsedSection(text="Paragraph alpha beta.", heading="Intro"),
        ParsedSection(
            text="A | B\nC | D",
            heading="Table 1",
            extra={"is_table": "true", "table_headers": "col1 | col2"},
        ),
        ParsedSection(text="See warranty schedule.", heading="Footnote 1"),
    ]
    document = ParsedDocument(
        source_path=Path("/tmp/doc.txt"),
        source_type="text",
        sections=sections,
    )

    chunks = chunk_document(document, settings)

    # Duplicate prose section should be deduped by SHA-256 hash
    prose_chunks = [chunk for chunk in chunks if chunk.extra.get("chunking") == "prose"]
    assert len(prose_chunks) == 1

    # Table chunk should serialise rows and include metadata
    table_chunks = [chunk for chunk in chunks if chunk.extra.get("chunking") == "table_row"]
    assert table_chunks, "expected table row chunks"
    first_table = table_chunks[0]
    assert first_table.extra["table_headers"] == "col1 | col2"
    assert first_table.extra["chunk_sha"] == first_table.sha256

    # Footnote chunk retains chunking label and SHA metadata
    footnote = next(chunk for chunk in chunks if chunk.extra.get("chunking") == "footnote")
    assert footnote.extra["chunk_sha"] == footnote.sha256


def test_chunker_assigns_traceable_metadata() -> None:
    settings = AppSettings(chunk_target_tokens=64, chunk_min_tokens=0)
    sections = [
        ParsedSection(
            text="Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod.",
            heading="Overview",
            breadcrumbs=["Section 1"],
        ),
    ]
    document = ParsedDocument(
        source_path=Path("/tmp/manual.txt"),
        source_type="manual",
        sections=sections,
    )

    chunks = chunk_document(document, settings)
    assert len(chunks) >= 1
    for chunk in chunks:
        assert chunk.extra["chunk_sha"] == chunk.sha256
        assert "breadcrumbs" in chunk.extra
        assert chunk.extra.get("source_type") == "manual"
