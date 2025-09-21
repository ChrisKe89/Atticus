"""Ingestion pipeline entry point."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, Iterable, List

from ..config import Settings
from ..embedding import EmbeddingClient
from ..index.storage import build_index, write_index
from ..logging_utils import configure_logging, log_event
from .chunker import Chunk, chunk_documents
from .parser import Document, load_documents


def run_ingestion(settings: Settings | None = None) -> Dict[str, object]:
    """Execute the ingestion pipeline end-to-end."""

    settings = settings or Settings()
    logger = configure_logging(settings)

    start_time = time.time()
    documents: List[Document] = load_documents(settings.content_root)
    chunks: List[Chunk] = chunk_documents(documents, settings)

    embed_client = EmbeddingClient(settings, logger=logger)
    embeddings = embed_client.embed_texts(f"{chunk.document_id} {chunk.text}" for chunk in chunks)

    index_payload = build_index(chunks, embeddings, settings)
    paths = write_index(index_payload, settings)
    elapsed = time.time() - start_time

    summary: Dict[str, object] = {
        "documents": len(documents),
        "chunks": len(chunks),
        "embedding_model": embed_client.model_name,
        "embedding_dimension": embed_client.dimension,
        "index_path": str(paths["index"]),
        "snapshot_path": str(paths["snapshot"]),
        "elapsed_seconds": round(elapsed, 2),
    }

    log_event(logger, "ingestion_complete", **summary)
    return summary
