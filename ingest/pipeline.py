"""Ingestion pipeline orchestrating parsing, chunking, and indexing."""

from __future__ import annotations

import json
import shutil
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from atticus.config import AppSettings, Manifest, load_manifest, load_settings, write_manifest
from atticus.embeddings import EmbeddingClient
from atticus.logging import configure_logging, log_event
from atticus.utils import sha256_file, sha256_text
from atticus.vector_db import PgVectorRepository, StoredChunk, save_metadata
from retriever.models import ModelCatalog, extract_models, load_model_catalog

from .chunker import chunk_document
from .models import Chunk as ParsedChunk
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


def _build_document_scope(
    documents: Sequence[ParsedDocument], catalog: ModelCatalog
) -> dict[str, dict[str, set[str]]]:
    scope: dict[str, dict[str, set[str]]] = {}
    for document in documents:
        texts: list[str] = [document.source_path.name]
        for section in document.sections[:5]:
            if section.heading:
                texts.append(section.heading)
            texts.append(section.text)
        models: set[str] = set()
        families: set[str] = set()
        for text in texts:
            if not text:
                continue
            extraction = extract_models(text, catalog=catalog)
            models.update(extraction.models)
            families.update(extraction.families)
        scope[document.document_id] = {"models": models, "families": families}
    return scope


def _annotate_chunk_with_catalog(
    chunk: StoredChunk | ParsedChunk,
    catalog: ModelCatalog,
    document_scope: dict[str, dict[str, set[str]]],
) -> None:
    texts = [
        getattr(chunk, "text", "") or "",
        chunk.extra.get("breadcrumbs", ""),
        getattr(chunk, "source_path", "") or "",
    ]
    models: set[str] = set()
    families: set[str] = set()
    for text in texts:
        if not text:
            continue
        extraction = extract_models(text, catalog=catalog)
        models.update(extraction.models)
        families.update(extraction.families)

    defaults = document_scope.get(chunk.document_id)
    if defaults:
        models.update(defaults.get("models", set()))
        families.update(defaults.get("families", set()))

    if not families and models:
        for model in models:
            ident = catalog.match_model(model)
            if ident:
                families.add(ident.family_id)

    if families:
        family_ids = sorted(families)
        chunk.extra["product_family"] = ",".join(family_ids)
        labels = {
            catalog.families[family_id].label
            for family_id in family_ids
            if family_id in catalog.families
        }
        if labels:
            chunk.extra["product_family_label"] = ", ".join(sorted(labels))

    if models:
        chunk.extra["models"] = json.dumps(sorted(models))


def _snapshot_directory(settings: AppSettings, timestamp: str) -> Path:
    safe = timestamp.replace(":", "").replace("-", "")
    snapshot_dir = settings.snapshots_dir / safe
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    return snapshot_dir


def ingest_corpus(  # noqa: PLR0915, PLR0912
    settings: AppSettings | None = None, options: IngestionOptions | None = None
) -> IngestionSummary:
    settings = settings or load_settings()
    options = options or IngestionOptions()
    settings.ensure_directories()
    logger = configure_logging(settings)
    catalog = load_model_catalog()

    if not settings.database_url:
        raise ValueError("DATABASE_URL must be configured before running ingestion")

    repo = PgVectorRepository(settings)
    repo.ensure_schema()

    ingest_time = settings.timestamp()
    start_time = time.time()
    manifest = load_manifest(settings.manifest_path)

    target_paths = (
        list(options.paths) if options.paths else list(discover_documents(settings.content_dir))
    )
    previous_docs = manifest.documents if manifest else {}

    reused_chunks: list[StoredChunk] = []
    reused_documents: dict[str, dict[str, Any]] = {}
    new_documents: list[ParsedDocument] = []
    skipped = 0
    document_lookup: dict[str, str] = {}

    for raw_path in target_paths:
        file_path = Path(raw_path)
        file_hash = sha256_file(file_path)
        manifest_entry = (
            previous_docs.get(str(file_path)) if manifest and not options.full_refresh else None
        )
        if manifest_entry and manifest_entry.get("sha256") == file_hash:
            existing_chunks = repo.fetch_chunks_for_source(str(file_path))
            if existing_chunks:
                for existing_chunk in existing_chunks:
                    existing_chunk.extra["embedding_model"] = settings.embed_model
                    existing_chunk.extra["embedding_model_version"] = (
                        settings.embedding_model_version
                    )
                    existing_chunk.extra["ingested_at"] = ingest_time
                    existing_chunk.extra.setdefault("chunk_sha", existing_chunk.sha256)
                reused_chunks.extend(existing_chunks)
                first = existing_chunks[0]
                reused_documents[first.document_id] = {
                    "document_id": first.document_id,
                    "source_path": str(file_path),
                    "sha256": str(manifest_entry.get("sha256", "")),
                    "source_type": manifest_entry.get("source_type"),
                    "chunks": existing_chunks,
                }
                document_lookup[str(file_path)] = str(manifest_entry.get("source_type", ""))
                skipped += 1
                continue
        document = parse_document(file_path)
        document.sha256 = file_hash
        new_documents.append(document)
        document_lookup[str(document.source_path)] = document.source_type

    new_parsed_chunks: list[ParsedChunk] = []
    for document in new_documents:
        new_parsed_chunks.extend(chunk_document(document, settings))

    document_scope = _build_document_scope(new_documents, catalog)
    for parsed_chunk in new_parsed_chunks:
        _annotate_chunk_with_catalog(parsed_chunk, catalog, document_scope)
    for reused_chunk in reused_chunks:
        _annotate_chunk_with_catalog(reused_chunk, catalog, document_scope)

    embed_client = EmbeddingClient(settings, logger=logger)
    embeddings = embed_client.embed_texts(chunk.text for chunk in new_parsed_chunks)

    stored_chunks: list[StoredChunk] = list(reused_chunks)
    chunks_by_document: dict[str, list[StoredChunk]] = {}
    for doc_id, info in reused_documents.items():
        chunks_by_document[doc_id] = list(info["chunks"])

    for index_counter, (parsed_chunk, embedding) in enumerate(
        zip(new_parsed_chunks, embeddings, strict=False), start=len(stored_chunks)
    ):
        metadata = {key: str(value) for key, value in parsed_chunk.extra.items()}
        metadata.setdefault("chunk_sha", parsed_chunk.sha256)
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
        chunk_object = StoredChunk(
            chunk_id=parsed_chunk.chunk_id,
            document_id=parsed_chunk.document_id,
            source_path=parsed_chunk.source_path,
            text=parsed_chunk.text,
            start_token=parsed_chunk.start_token,
            end_token=parsed_chunk.end_token,
            page_number=parsed_chunk.page_number,
            section=parsed_chunk.heading,
            sha256=parsed_chunk.sha256,
            embedding=list(embedding),
            extra=metadata,
        )
        stored_chunks.append(chunk_object)
        chunks_by_document.setdefault(parsed_chunk.document_id, []).append(chunk_object)

    for info in reused_documents.values():
        repo.replace_document(
            document_id=info["document_id"],
            source_path=info["source_path"],
            sha256=info["sha256"],
            source_type=info.get("source_type"),
            chunks=info["chunks"],
            ingest_time=ingest_time,
        )

    for document in new_documents:
        repo.replace_document(
            document_id=document.document_id,
            source_path=str(document.source_path),
            sha256=document.sha256 or "",
            source_type=document.source_type,
            chunks=chunks_by_document.get(document.document_id, []),
            ingest_time=ingest_time,
        )

    save_metadata(stored_chunks, settings.metadata_path)

    snapshot_dir = _snapshot_directory(settings, ingest_time)
    shutil.copy2(settings.metadata_path, snapshot_dir / "index_metadata.json")

    document_records: dict[str, dict[str, Any]] = {}
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

    previous_paths = set(previous_docs.keys())
    current_paths = set(document_records.keys())
    removed_paths = previous_paths - current_paths
    for missing_path in removed_paths:
        repo.remove_document(missing_path)

    document_hashes = [
        f"{path}:{info.get('sha256', '')}" for path, info in sorted(document_records.items())
    ]
    corpus_hash = (
        sha256_text("|".join(document_hashes)) if document_hashes else sha256_text("empty")
    )

    index_identifier = Path("pgvector")
    metadata_snapshot_path = snapshot_dir / "index_metadata.json"

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
        index_path=index_identifier,
        snapshot_path=metadata_snapshot_path,
        documents=document_records,
    )
    write_manifest(settings.manifest_path, manifest)
    shutil.copy2(settings.manifest_path, snapshot_dir / "manifest.json")

    elapsed = time.time() - start_time
    summary = IngestionSummary(
        documents_processed=len(new_documents),
        documents_skipped=skipped,
        chunks_indexed=len(stored_chunks),
        elapsed_seconds=round(elapsed, 2),
        manifest_path=settings.manifest_path,
        index_path=index_identifier,
        snapshot_path=metadata_snapshot_path,
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
