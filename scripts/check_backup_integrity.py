"""Validate a restored Atticus database contains expected structures."""

from __future__ import annotations

import os
import subprocess
import sys
from typing import Iterable

import psycopg
from psycopg import Cursor


REQUIRED_INDEXES: tuple[str, ...] = (
    "idx_atticus_chunks_document",
    "idx_atticus_chunks_source_path",
    "idx_atticus_chunks_doc_sha",
    "idx_atticus_chunks_metadata_category",
    "idx_atticus_chunks_metadata_product",
    "idx_atticus_chunks_metadata_product_family",
    "idx_atticus_chunks_metadata_version",
    "idx_atticus_chunks_metadata_org",
    "idx_atticus_chunks_metadata_acl",
)


def _run_db_verify(database_url: str) -> None:
    env = os.environ.copy()
    env.setdefault("DATABASE_URL", database_url)
    subprocess.run([sys.executable, "scripts/db_verify.py"], check=True, env=env)


def _assert_indexes(cursor: Cursor, index_names: Iterable[str]) -> None:
    missing: list[str] = []
    for name in index_names:
        cursor.execute(
            "SELECT 1 FROM pg_indexes WHERE indexname = %s",
            (name,),
        )
        if cursor.fetchone() is None:
            missing.append(name)
    if missing:
        raise RuntimeError(f"Missing expected indexes: {', '.join(missing)}")


def main() -> int:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL must be set for backup integrity checks", flush=True)
        return 1

    _run_db_verify(database_url)

    with psycopg.connect(database_url) as conn:  # type: ignore[arg-type]
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM atticus_documents")
            document_count = cur.fetchone()
            if not document_count:
                raise RuntimeError("atticus_documents table returned no result")

            cur.execute("SELECT COUNT(*) FROM atticus_chunks")
            chunk_count = cur.fetchone()
            if not chunk_count:
                raise RuntimeError("atticus_chunks table returned no result")

            cur.execute("SELECT SUM(chunk_count) FROM atticus_documents")
            chunk_total = cur.fetchone() or (0,)
            if chunk_total[0] is not None and chunk_count[0] is not None:
                if chunk_total[0] < chunk_count[0]:
                    raise RuntimeError("Chunk totals per document should be >= persisted chunks")

            _assert_indexes(cur, REQUIRED_INDEXES)

    print("Backup integrity checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
