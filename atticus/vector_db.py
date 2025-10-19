"""Postgres/pgvector persistence helpers."""

from __future__ import annotations

import json
import logging
from collections.abc import Iterable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import psycopg
from pgvector.psycopg import Vector, register_vector
from psycopg.rows import dict_row
from psycopg.types.json import Json

from core.config import AppSettings

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class StoredChunk:
    """Chunk payload with embedding and metadata."""

    chunk_id: str
    document_id: str
    source_path: str
    text: str
    start_token: int
    end_token: int
    page_number: int | None
    section: str | None
    sha256: str
    embedding: Sequence[float] | None = None
    extra: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "source_path": self.source_path,
            "text": self.text,
            "start_token": self.start_token,
            "end_token": self.end_token,
            "page_number": self.page_number,
            "section": self.section,
            "sha256": self.sha256,
            "embedding": [float(value) for value in (self.embedding or [])],
            "extra": dict(self.extra),
        }


def save_metadata(chunks: Iterable[StoredChunk], path: Path) -> None:
    """Persist chunk metadata (including embeddings) to JSON."""

    serialised = [chunk.to_dict() for chunk in chunks]
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(serialised, indent=2, ensure_ascii=False) + "\n"
    path.write_text(payload, encoding="utf-8")


def load_metadata(path: Path) -> list[StoredChunk]:
    """Load chunk metadata from JSON snapshots."""

    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    result: list[StoredChunk] = []
    for item in payload:
        extra = item.get("extra", {}) or {}
        extra_str = {str(k): str(v) for k, v in extra.items()}
        embedding = item.get("embedding")
        sha_value = str(item.get("sha256", ""))
        result.append(
            StoredChunk(
                chunk_id=str(item["chunk_id"]),
                document_id=str(item["document_id"]),
                source_path=str(item["source_path"]),
                text=str(item.get("text", "")),
                start_token=int(item.get("start_token", 0)),
                end_token=int(item.get("end_token", 0)),
                page_number=item.get("page_number"),
                section=item.get("section"),
                sha256=sha_value,
                embedding=list(map(float, embedding)) if embedding is not None else None,
                extra=extra_str,
            )
        )
    return result


class PgVectorRepository:
    """Wrapper around psycopg/pgvector for chunk storage and retrieval."""

    def __init__(self, settings: AppSettings) -> None:
        if not settings.database_url:
            raise ValueError("DATABASE_URL must be configured for pgvector usage")
        self.settings = settings

    @contextmanager
    def connection(self, *, autocommit: bool = False) -> Iterator[psycopg.Connection]:
        conn = psycopg.connect(
            self.settings.database_url,
            autocommit=autocommit,
            row_factory=dict_row,
        )
        register_vector(conn)
        try:
            yield conn
            if not autocommit:
                conn.commit()
        except Exception:
            if not autocommit:
                conn.rollback()
            raise
        finally:
            conn.close()

    def ensure_schema(self) -> None:
        """Create pgvector extension, tables, and indexes if they do not exist."""

        lists = max(1, int(self.settings.pgvector_lists))
        dimension = int(self.settings.embed_dimensions)
        ann_supported = dimension <= 2000
        with self.connection(autocommit=True) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS atticus_documents (
                    document_id TEXT PRIMARY KEY,
                    source_path TEXT UNIQUE NOT NULL,
                    sha256 TEXT NOT NULL,
                    source_type TEXT,
                    metadata JSONB DEFAULT '{}'::jsonb,
                    chunk_count INTEGER DEFAULT 0,
                    ingested_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS atticus_chunks (
                    chunk_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL REFERENCES atticus_documents(document_id) ON DELETE CASCADE,
                    source_path TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    section TEXT,
                    page_number INTEGER,
                    token_count INTEGER,
                    start_token INTEGER,
                    end_token INTEGER,
                    sha256 TEXT NOT NULL,
                    metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                    embedding vector({dimension}) NOT NULL,
                    ingested_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                "ALTER TABLE atticus_chunks ADD COLUMN IF NOT EXISTS sha256 TEXT NOT NULL DEFAULT ''"
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_atticus_chunks_document
                ON atticus_chunks(document_id)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_atticus_chunks_source_path
                ON atticus_chunks(source_path)
                """
            )
            conn.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_atticus_chunks_doc_sha
                ON atticus_chunks(document_id, sha256)
                """
            )
            metadata_index_definitions = {
                "idx_atticus_chunks_metadata_category": "metadata ->> 'category'",
                "idx_atticus_chunks_metadata_product": "metadata ->> 'product'",
                "idx_atticus_chunks_metadata_product_family": "metadata ->> 'product_family'",
                "idx_atticus_chunks_metadata_version": "metadata ->> 'version'",
                "idx_atticus_chunks_metadata_org": "metadata ->> 'org_id'",
                "idx_atticus_chunks_metadata_acl": "metadata ->> 'acl'",
            }
            for index_name, expression in metadata_index_definitions.items():
                conn.execute(
                    f"""
                    CREATE INDEX IF NOT EXISTS {index_name}
                    ON atticus_chunks (({expression}))
                    """
                )
            if ann_supported:
                conn.execute(
                    f"""
                    CREATE INDEX IF NOT EXISTS idx_atticus_chunks_embedding
                    ON atticus_chunks USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = {lists})
                    """
                )
            else:
                logger.warning(
                    "Skipping ivfflat index on atticus_chunks.embedding; "
                    "dimension %s exceeds the 2000 limit for this pgvector build. "
                    "Install a pgvector build compiled with a higher INDEX_MAX_DIMENSIONS "
                    "to enable ANN search.",
                    dimension,
                )
            conn.execute(
                "ALTER TABLE atticus_documents ALTER COLUMN metadata SET DEFAULT '{}'::jsonb"
            )
            conn.execute("ALTER TABLE atticus_chunks ALTER COLUMN metadata SET DEFAULT '{}'::jsonb")
            conn.execute("ANALYZE atticus_chunks")
            conn.execute("ANALYZE atticus_chunks")

    def fetch_document(self, source_path: str) -> dict[str, Any] | None:
        with self.connection() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT document_id, sha256, source_type, chunk_count FROM atticus_documents WHERE source_path = %s",
                (source_path,),
            )
            return cur.fetchone()

    def remove_document(self, source_path: str) -> None:
        """Delete a document (and its chunks) by source path if it exists."""
        record = self.fetch_document(source_path)
        if not record:
            return
        with self.connection() as conn, conn.cursor() as cur:
            cur.execute(
                "DELETE FROM atticus_documents WHERE document_id = %s", (record["document_id"],)
            )

    def fetch_chunks_for_source(self, source_path: str) -> list[StoredChunk]:
        with self.connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT chunk_id, document_id, source_path, text, start_token, end_token,
                       page_number, section, sha256, metadata, embedding
                FROM atticus_chunks
                WHERE source_path = %s
                ORDER BY position ASC
                """,
                (source_path,),
            )
            rows = cur.fetchall()
        chunks: list[StoredChunk] = []
        for row in rows:
            metadata = row.get("metadata") or {}
            if isinstance(metadata, dict):
                meta = {str(k): str(v) for k, v in metadata.items()}
            else:
                meta = {}
            embedding = row.get("embedding")
            embedding_list: Sequence[float] | None
            if embedding is None:
                embedding_list = None
            else:
                embedding_list = list(embedding)
            chunks.append(
                StoredChunk(
                    chunk_id=str(row["chunk_id"]),
                    document_id=str(row["document_id"]),
                    source_path=str(row["source_path"]),
                    text=str(row["text"]),
                    start_token=int(row.get("start_token") or 0),
                    end_token=int(row.get("end_token") or 0),
                    page_number=row.get("page_number"),
                    section=row.get("section"),
                    sha256=str(row.get("sha256", "")),
                    embedding=embedding_list,
                    extra=meta,
                )
            )
        return chunks

    def load_all_chunk_metadata(self) -> list[StoredChunk]:
        with self.connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT chunk_id, document_id, source_path, text, start_token, end_token,
                       page_number, section, sha256, metadata
                FROM atticus_chunks
                ORDER BY position ASC
                """
            )
            rows = cur.fetchall()
        result: list[StoredChunk] = []
        for row in rows:
            metadata = row.get("metadata") or {}
            meta = (
                {str(k): str(v) for k, v in metadata.items()} if isinstance(metadata, dict) else {}
            )
            result.append(
                StoredChunk(
                    chunk_id=str(row["chunk_id"]),
                    document_id=str(row["document_id"]),
                    source_path=str(row["source_path"]),
                    text=str(row["text"]),
                    start_token=int(row.get("start_token") or 0),
                    end_token=int(row.get("end_token") or 0),
                    page_number=row.get("page_number"),
                    section=row.get("section"),
                    sha256=str(row.get("sha256", "")),
                    embedding=None,
                    extra=meta,
                )
            )
        return result

    def replace_document(
        self,
        *,
        document_id: str,
        source_path: str,
        sha256: str,
        source_type: str | None,
        chunks: Sequence[StoredChunk],
        ingest_time: str,
    ) -> None:
        metadata = {"ingested_at": ingest_time, "source_type": source_type or ""}
        with self.connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO atticus_documents (document_id, source_path, sha256, source_type, metadata, chunk_count, ingested_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s::timestamptz, %s::timestamptz)
                ON CONFLICT (document_id)
                DO UPDATE SET
                    source_path = EXCLUDED.source_path,
                    sha256 = EXCLUDED.sha256,
                    source_type = EXCLUDED.source_type,
                    metadata = EXCLUDED.metadata,
                    chunk_count = EXCLUDED.chunk_count,
                    ingested_at = EXCLUDED.ingested_at,
                    updated_at = EXCLUDED.updated_at
                """,
                (
                    document_id,
                    source_path,
                    sha256,
                    source_type,
                    Json(metadata),
                    len(chunks),
                    ingest_time,
                    ingest_time,
                ),
            )
            cur.execute("DELETE FROM atticus_chunks WHERE document_id = %s", (document_id,))
            for position, chunk in enumerate(chunks):
                if chunk.embedding is None:
                    raise ValueError(f"Chunk {chunk.chunk_id} missing embedding for persistence")
                meta = {str(k): str(v) for k, v in chunk.extra.items()}
                token_count = meta.get("token_count")
                try:
                    token_value = int(token_count) if token_count is not None else None
                except ValueError:
                    token_value = None
                cur.execute(
                    """
                    INSERT INTO atticus_chunks (
                        chunk_id,
                        document_id,
                        source_path,
                        position,
                        text,
                        section,
                        page_number,
                        token_count,
                        start_token,
                        end_token,
                        sha256,
                        metadata,
                        embedding,
                        ingested_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::timestamptz)
                    """,
                    (
                        chunk.chunk_id,
                        document_id,
                        source_path,
                        position,
                        chunk.text,
                        chunk.section,
                        chunk.page_number,
                        token_value,
                        chunk.start_token,
                        chunk.end_token,
                        chunk.sha256,
                        Json(meta),
                        Vector(chunk.embedding),
                        ingest_time,
                    ),
                )

    def query_similar_chunks(
        self,
        embedding: Sequence[float],
        *,
        limit: int,
        probes: int | None = None,
    ) -> list[dict[str, Any]]:
        with self.connection() as conn, conn.cursor() as cur:
            if probes and probes > 0:
                cur.execute(f"SET LOCAL ivfflat.probes = {int(probes)}")
            cur.execute(
                """
                SELECT chunk_id, document_id, source_path, text, metadata, page_number, section,
                       embedding <=> %s AS distance
                FROM atticus_chunks
                ORDER BY distance
                LIMIT %s
                """,
                (Vector(embedding), limit),
            )
            rows = cur.fetchall()
        formatted: list[dict[str, Any]] = []
        for row in rows:
            metadata = row.get("metadata") or {}
            meta = (
                {str(k): str(v) for k, v in metadata.items()} if isinstance(metadata, dict) else {}
            )
            formatted.append(
                {
                    "chunk_id": str(row["chunk_id"]),
                    "document_id": str(row["document_id"]),
                    "source_path": str(row["source_path"]),
                    "text": str(row.get("text", "")),
                    "page_number": row.get("page_number"),
                    "section": row.get("section"),
                    "metadata": meta,
                    "distance": float(row.get("distance", 0.0)),
                }
            )
        return formatted

    def truncate(self) -> None:
        """Delete all stored documents and chunks."""

        with self.connection() as conn, conn.cursor() as cur:
            cur.execute("TRUNCATE atticus_chunks, atticus_documents")
