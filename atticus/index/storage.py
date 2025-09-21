"""Index persistence utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List

from ..config import Settings
from ..ingestion.chunker import Chunk


def build_index(chunks: Iterable[Chunk], embeddings: Iterable[List[float]], settings: Settings) -> Dict:
    """Combine chunks and embeddings into a serializable index."""

    entries = []
    for chunk, vector in zip(chunks, embeddings):
        entries.append(
            {
                "id": chunk.chunk_id,
                "document_path": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "start_token": chunk.start_token,
                "end_token": chunk.end_token,
                "text": chunk.text,
                "embedding": vector,
            }
        )

    index_payload: Dict[str, object] = {
        "created_at": settings.timestamp(),
        "embedding_model": settings.embedding_model,
        "embedding_model_version": settings.embedding_model,
        "embedding_dimension": settings.embedding_dimension,
        "chunk_size": settings.chunk_size,
        "chunk_overlap": settings.chunk_overlap,
        "chunk_count": len(entries),
        "entries": entries,
    }
    return index_payload


def write_index(index_payload: Dict, settings: Settings) -> Dict[str, Path]:
    """Persist the index to disk and create a snapshot."""

    index_path = Path(settings.index_path)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path = settings.next_snapshot_path()
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)

    for path in (index_path, snapshot_path):
        path.write_text(json.dumps(index_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    return {"index": index_path, "snapshot": snapshot_path}
