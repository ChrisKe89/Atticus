"""Generate a lightweight seed manifest from the current CED corpus."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:  # pragma: no cover - optional dependency
    import psycopg  # type: ignore
    import pgvector.psycopg  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - lightweight fallback for seed generation
    import types

    psycopg = types.ModuleType("psycopg")
    psycopg.rows = types.SimpleNamespace(dict_row=None)
    psycopg.types = types.SimpleNamespace(json=types.SimpleNamespace(Json=lambda value: value))
    psycopg.connect = lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("psycopg unavailable"))
    sys.modules.setdefault("psycopg", psycopg)

    pgvector = types.ModuleType("pgvector")
    sys.modules.setdefault("pgvector", pgvector)

    pgvector_psycopg = types.ModuleType("pgvector.psycopg")
    pgvector_psycopg.register_vector = lambda conn: None
    pgvector_psycopg.Vector = list
    sys.modules["pgvector.psycopg"] = pgvector_psycopg

    ingest_pkg = types.ModuleType("ingest")
    ingest_pkg.__path__ = [str(ROOT / "ingest")]
    sys.modules.setdefault("ingest", ingest_pkg)

    sys.modules.setdefault("camelot", types.SimpleNamespace(read_pdf=lambda *args, **kwargs: []))
    sys.modules.setdefault("tabula", types.SimpleNamespace(read_pdf=lambda *args, **kwargs: []))

from atticus.config import load_settings
from atticus.utils import sha256_file
from ingest.chunker import chunk_document
from ingest.parsers import discover_documents, parse_document


def build_seed_manifest() -> list[dict[str, object]]:
    settings = load_settings()
    settings.ensure_directories()
    manifest: list[dict[str, object]] = []
    for index, path in enumerate(discover_documents(settings.content_dir)):
        document = parse_document(path)
        document.sha256 = sha256_file(path)
        chunks = chunk_document(document, settings)
        manifest.append(
            {
                "document": str(path),
                "sha256": document.sha256,
                "source_type": document.source_type,
                "chunk_count": len(chunks),
                "chunks": [
                    {
                        "chunk_id": chunk.chunk_id,
                        "sha256": chunk.sha256,
                        "heading": chunk.heading,
                        "chunking": chunk.extra.get("chunking"),
                        "page_number": chunk.page_number,
                    }
                    for chunk in chunks[:25]
                ],
            }
        )
        if index >= 9:  # keep seed small
            break
    return manifest


def main() -> None:
    output_path = Path("seeds/seed_manifest.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = build_seed_manifest()
    output_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote seed manifest with {len(manifest)} documents to {output_path}")


if __name__ == "__main__":
    main()
