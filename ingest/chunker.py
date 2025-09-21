"""Chunking utilities for parsed documents."""

from __future__ import annotations

from typing import Iterable, List

from atticus.config import AppSettings
from atticus.tokenization import decode, encode, split_tokens

from .models import Chunk, ParsedDocument


def chunk_document(document: ParsedDocument, settings: AppSettings) -> List[Chunk]:
    chunks: List[Chunk] = []
    chunk_counter = 0
    for section in document.sections:
        tokens = encode(section.text)
        if not tokens:
            continue
        for start, end in split_tokens(tokens, settings.chunk_size, settings.chunk_overlap_tokens):
            text = decode(tokens[start:end])
            chunk_id = f"{document.document_id}::chunk_{chunk_counter}"
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    document_id=document.document_id,
                    source_path=str(document.source_path),
                    text=text,
                    start_token=start,
                    end_token=end,
                    page_number=section.page_number,
                    heading=section.heading,
                    extra=section.extra.copy(),
                )
            )
            chunk_counter += 1
    return chunks


def chunk_documents(documents: Iterable[ParsedDocument], settings: AppSettings) -> List[Chunk]:
    all_chunks: List[Chunk] = []
    for document in documents:
        all_chunks.extend(chunk_document(document, settings))
    return all_chunks

