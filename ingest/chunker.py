"""Chunking utilities for parsed documents."""

from __future__ import annotations

from collections.abc import Iterable

from atticus.config import AppSettings
from atticus.tokenization import decode, encode, split_tokens

from .models import Chunk, ParsedDocument

MIN_CHUNK_MERGE_COUNT = 2


def chunk_document(document: ParsedDocument, settings: AppSettings) -> list[Chunk]:
    chunks: list[Chunk] = []
    chunk_counter = 0
    document_trail = [document.source_path.name]
    target_tokens = settings.chunk_target_tokens or settings.chunk_size
    overlap_tokens = settings.chunk_overlap_tokens
    min_tokens = settings.chunk_min_tokens
    for section in document.sections:
        tokens = encode(section.text)
        if not tokens:
            continue
        breadcrumbs = document_trail + list(section.breadcrumbs)
        if section.heading and (not breadcrumbs or breadcrumbs[-1] != section.heading):
            breadcrumbs.append(section.heading)
        metadata = section.extra.copy()
        metadata.setdefault("source_type", document.source_type)
        if section.heading:
            metadata.setdefault("section_heading", section.heading)
        if section.page_number is not None:
            metadata.setdefault("page_number", str(section.page_number))
        breadcrumb_label = " > ".join(breadcrumbs)
        if breadcrumb_label:
            metadata.setdefault("breadcrumbs", breadcrumb_label)
        splits = list(split_tokens(tokens, target_tokens, overlap_tokens))
        for start, end in splits:
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
                    extra=metadata.copy(),
                    breadcrumbs=breadcrumbs,
                )
            )
            chunk_counter += 1
        if min_tokens > 0 and chunks:
            # merge small trailing chunk if needed
            last_chunk = chunks[-1]
            if (
                last_chunk.end_token - last_chunk.start_token < min_tokens
                and len(chunks) >= MIN_CHUNK_MERGE_COUNT
            ):
                prev = chunks[-2]
                prev.text = f"{prev.text}\n{last_chunk.text}".strip()
                prev.end_token = last_chunk.end_token
                prev.extra.update(last_chunk.extra)
                prev.breadcrumbs.extend(
                    x for x in last_chunk.breadcrumbs if x not in prev.breadcrumbs
                )
                chunks.pop()
    return chunks


def chunk_documents(documents: Iterable[ParsedDocument], settings: AppSettings) -> list[Chunk]:
    all_chunks: list[Chunk] = []
    for document in documents:
        all_chunks.extend(chunk_document(document, settings))
    return all_chunks
