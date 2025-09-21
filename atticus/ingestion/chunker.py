"""Chunking utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from ..config import Settings


@dataclass(slots=True)
class Chunk:
    """Represents a chunk of a document."""

    document_id: str
    chunk_id: str
    text: str
    chunk_index: int
    start_token: int
    end_token: int


def chunk_document(text: str, settings: Settings, document_id: str) -> List[Chunk]:
    """Chunk a document using the configured window and overlap."""

    tokens = text.split()
    if not tokens:
        return []

    window = settings.chunk_size
    overlap = settings.overlap_tokens()
    step = max(1, window - overlap)

    chunks: List[Chunk] = []
    for start in range(0, len(tokens), step):
        end = min(start + window, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = " ".join(chunk_tokens)
        chunk_index = len(chunks)
        chunk_id = f"{document_id}::chunk_{chunk_index}"
        chunks.append(
            Chunk(
                document_id=document_id,
                chunk_id=chunk_id,
                text=chunk_text,
                chunk_index=chunk_index,
                start_token=start,
                end_token=end,
            )
        )
        if end == len(tokens):
            break

    return chunks


def chunk_documents(documents: Iterable, settings: Settings) -> List[Chunk]:
    """Chunk all documents."""

    all_chunks: List[Chunk] = []
    for doc in documents:
        doc_chunks = chunk_document(doc.text, settings, doc.document_id)
        if doc_chunks:
            all_chunks.extend(doc_chunks)
    return all_chunks
