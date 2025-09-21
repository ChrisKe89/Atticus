"""Document parsing for ingestion."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

SUPPORTED_EXTENSIONS = {".txt", ".md"}


@dataclass(slots=True)
class Document:
    """Represents a parsed document ready for chunking."""

    path: Path
    text: str

    @property
    def document_id(self) -> str:
        return str(self.path)


def discover_documents(content_root: Path) -> Iterable[Path]:
    """Yield supported document paths under the content root."""

    for path in sorted(content_root.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield path


def parse_document(path: Path) -> Document:
    """Parse a single document into plain text."""

    text = path.read_text(encoding="utf-8")
    return Document(path=path, text=text)


def load_documents(content_root: Path) -> List[Document]:
    """Load all supported documents from the content root."""

    documents = [parse_document(path) for path in discover_documents(content_root)]
    return documents
