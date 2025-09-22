"""Ingestion pipeline orchestrating parsing, chunking, and indexing."""

from __future__ import annotations

import shutil
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from atticus.config import AppSettings, Manifest, load_manifest, load_settings, write_manifest
from atticus.embeddings import EmbeddingClient
from atticus.faiss_index import (
    StoredChunk,
    build_faiss_index,
    load_metadata,
    save_faiss_index,
    save_metadata,
)
from atticus.logging import configure_logging, log_event
from atticus.utils import sha256_file, sha256_text

from .chunker import chunk_document
from .models import ParsedDocument
from .parsers import discover_documents, parse_document


@dataclass(slots=True)
class IngestionOptions:
    full_refresh: bool = False
    paths: Sequence[Path] | None = None


@dataclass(slots=True)
class IngestionSummary:
    documents_processed: int
    documents_skipped: int
    chunks_indexed: int
    elapsed_seconds: float
    manifest_path: Path
    index_path: Path
    snapshot_path: Path
    ingested_at: str
    embedding_model: str
    embedding_model_version: str


def _snapshot_directory(settings: AppSettings, timestamp: str) -> Path:
    safe = timestamp.replace(":", "").replace("-", "")
    snapshot_dir = settings.snapshots_dir / safe
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    return snapshot_dir


def _reuse_chunks(metadata: list[StoredChunk], path: str) -> list[StoredChunk]:
    return [chunk for chunk in metadata if chunk.source_path == path]


def ingest_corpus(  # noqa: PLR0915, PLR0912
    settings: AppSettings | None = None, options: IngestionOptions | None = None
) -> IngestionSummary:
    settings = settings or load_settings()
    options = options or IngestionOptions()
    settings.ensure_directories()
    logger = configure_logging(settings)

    ingest_time = settings.timestamp()
    start_time = time.time()
    manifest = load_manifest(settings.manifest_path)
    existing_metadata = load_metadata(settings.metadata_path)

    target_paths = (
        list(options.paths) if options.paths else list(discover_documents(settings.content_dir))
    )
    previous_docs = manifest.documents if manifest else {}

    reused_chunks: list[StoredChunk] = []
    new_documents: list[ParsedDocument] = []
    skipped = 0

    for raw_path in target_paths:
        file_path = Path(raw_path)
        file_hash = sha256_file(file_path)
        manifest_entry = (
            previous_docs.get(str(file_path)) if manifest and not options.full_refresh else None
        )
        if manifest_entry and manifest_entry.get("sha256") == file_hash:
            reused = _reuse_chunks(existing_metadata, str(file_path))
            if reused:
                for item in reused:
                    item.extra.setdefault("embedding_model", settings.embed_model)
                    item.extra.setdefault(
                        "embedding_model_version", settings.embedding_model_version
                    )
                reused_chunks.extend(reused)
                skipped += 1
                continue
        document = parse_document(file_path)
        document.sha256 = file_hash
        new_documents.append(document)

    document_lookup: dict[str, str] = {}
    for chunk in reused_chunks:
        manifest_entry = previous_docs.get(chunk.source_path, {})
        document_lookup[chunk.source_path] = str(manifest_entry.get("source_type", ""))

    new_chunks = []
    for document in new_documents:
        document_lookup[str(document.source_path)] = document.source_type
        new_chunks.extend(chunk_document(document, settings))

    embed_client = EmbeddingClient(settings, logger=logger)
    embeddings = embed_client.embed_texts(chunk.text for chunk in new_chunks)

    stored_chunks: list[StoredChunk] = list(reused_chunks)
    for index_counter, (parsed_chunk, embedding) in enumerate(
        zip(new_chunks, embeddings, strict=False), start=len(stored_chunks)
    ):
        metadata = {key: str(value) for key, value in parsed_chunk.extra.items()}
        if parsed_chunk.breadcrumbs:
            metadata.setdefault("breadcrumbs", " > ".join(parsed_chunk.breadcrumbs))
        metadata.setdefault("source_path", parsed_chunk.source_path)
        metadata.setdefault("document_id", parsed_chunk.document_id)
        metadata.setdefault("chunk_index", str(index_counter))
        metadata.setdefault(
            "source_type",
            metadata.get("source_type", document_lookup.get(parsed_chunk.source_path, "")),
        )
        metadata.setdefault("ingested_at", ingest_time)
        metadata.setdefault("embedding_model", settings.embed_model)
        metadata.setdefault("embedding_model_version", settings.embedding_model_version)
        metadata.setdefault("token_span", f"{parsed_chunk.start_token}:{parsed_chunk.end_token}")
        metadata.setdefault(
            "token_count", str(max(0, parsed_chunk.end_token - parsed_chunk.start_token))
        )
        stored_chunks.append(
            StoredChunk(
                chunk_id=parsed_chunk.chunk_id,
                document_id=parsed_chunk.document_id,
                source_path=parsed_chunk.source_path,
                text=parsed_chunk.text,
                start_token=parsed_chunk.start_token,
                end_token=parsed_chunk.end_token,
                page_number=parsed_chunk.page_number,
                section=parsed_chunk.heading,
                embedding=embedding,
                extra=metadata,
            )
        )

    index, _ = build_faiss_index(stored_chunks, settings.embed_dimensions)
    save_faiss_index(index, settings.faiss_index_path)
    save_metadata(stored_chunks, settings.metadata_path)

    snapshot_dir = _snapshot_directory(settings, ingest_time)
    shutil.copy2(settings.faiss_index_path, snapshot_dir / "index.faiss")
    shutil.copy2(settings.metadata_path, snapshot_dir / "index_metadata.json")

    document_records: dict[str, dict[str, object]] = {}
    for chunk in stored_chunks:
        entry = document_records.setdefault(
            chunk.source_path,
            {
                "sha256": previous_docs.get(chunk.source_path, {}).get("sha256")
                if manifest
                else None,
                "chunk_count": 0,
                "source_type": previous_docs.get(chunk.source_path, {}).get("source_type")
                if manifest
                else None,
            },
        )
        raw_count = entry.get("chunk_count", 0)
        if isinstance(raw_count, int):
            chunk_count = raw_count
        elif isinstance(raw_count, str) and raw_count.isdigit():
            chunk_count = int(raw_count)
        else:
            chunk_count = 0
        entry["chunk_count"] = chunk_count + 1

    for document in new_documents:
        record = document_records.setdefault(
            str(document.source_path),
            {"sha256": document.sha256, "chunk_count": 0, "source_type": document.source_type},
        )
        record["sha256"] = document.sha256
        record["source_type"] = document.source_type

    document_hashes = [
        f"{path}:{info.get('sha256', '')}" for path, info in sorted(document_records.items())
    ]
    corpus_hash = (
        sha256_text("|".join(document_hashes)) if document_hashes else sha256_text("empty")
    )

    manifest = Manifest(
        embedding_model=settings.embed_model,
        embedding_model_version=settings.embedding_model_version,
        embedding_dimensions=settings.embed_dimensions,
        chunk_size=settings.chunk_size,
        chunk_overlap_ratio=settings.chunk_overlap_ratio,
        corpus_hash=corpus_hash,
        document_count=len(document_records),
        chunk_count=len(stored_chunks),
        created_at=ingest_time,
        metadata_path=settings.metadata_path,
        index_path=settings.faiss_index_path,
        snapshot_path=snapshot_dir / "index.faiss",
        documents=document_records,
    )
    write_manifest(settings.manifest_path, manifest)

    elapsed = time.time() - start_time
    summary = IngestionSummary(
        documents_processed=len(new_documents),
        documents_skipped=skipped,
        chunks_indexed=len(stored_chunks),
        elapsed_seconds=round(elapsed, 2),
        manifest_path=settings.manifest_path,
        index_path=settings.faiss_index_path,
        snapshot_path=snapshot_dir / "index.faiss",
        ingested_at=ingest_time,
        embedding_model=settings.embed_model,
        embedding_model_version=settings.embedding_model_version,
    )

    log_event(
        logger,
        "ingestion_complete",
        documents_processed=summary.documents_processed,
        documents_skipped=summary.documents_skipped,
        chunks_indexed=summary.chunks_indexed,
        elapsed_seconds=summary.elapsed_seconds,
        embedding_model=settings.embed_model,
        embedding_model_version=settings.embedding_model_version,
        ingested_at=ingest_time,
    )

    return summary
