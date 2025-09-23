"""Helpers for building and persisting the FAISS vector store."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from pathlib import Path

import faiss
import numpy as np
import numpy.typing as npt


@dataclass(slots=True)
class StoredChunk:
    """Represents a chunk ready to be persisted with embedding metadata."""

    chunk_id: str
    document_id: str
    source_path: str
    text: str
    start_token: int
    end_token: int
    page_number: int | None
    section: str | None
    embedding: list[float]
    extra: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_faiss_index(
    chunks: Iterable[StoredChunk], dimension: int
) -> tuple[faiss.IndexFlatIP, npt.NDArray[np.float32]]:
    vectors: npt.NDArray[np.float32] = np.array(
        [chunk.embedding for chunk in chunks], dtype=np.float32
    )
    if vectors.size == 0:
        index = faiss.IndexFlatIP(dimension)
        return index, vectors

    index = faiss.IndexFlatIP(dimension)
    faiss.normalize_L2(vectors)
    index.add(x=vectors)  # pyright: ignore[reportCallIssue]
    return index, vectors


def save_faiss_index(index: faiss.IndexFlatIP, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(path))


def save_metadata(chunks: Iterable[StoredChunk], path: Path) -> None:
    data = [chunk.to_dict() for chunk in chunks]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_metadata(path: Path) -> list[StoredChunk]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    result: list[StoredChunk] = []
    for item in payload:
        result.append(
            StoredChunk(
                chunk_id=item["chunk_id"],
                document_id=item["document_id"],
                source_path=item["source_path"],
                text=item["text"],
                start_token=int(item.get("start_token", 0)),
                end_token=int(item.get("end_token", 0)),
                page_number=item.get("page_number"),
                section=item.get("section"),
                embedding=list(map(float, item["embedding"])),
                extra={k: str(v) for k, v in item.get("extra", {}).items()},
            )
        )
    return result


def load_faiss_index(path: Path, dimension: int) -> faiss.IndexFlatIP:
    if not path.exists():
        return faiss.IndexFlatIP(dimension)
    index = faiss.read_index(str(path))
    return index
