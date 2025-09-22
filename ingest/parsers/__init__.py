"""Document discovery and parsing utilities."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path

from ..models import ParsedDocument
from .docx import parse_docx
from .html import parse_html
from .image import parse_image
from .pdf import parse_pdf
from .text import parse_text
from .xlsx import parse_xlsx

Parser = Callable[[Path], ParsedDocument]

PARSERS: dict[str, Parser] = {
    ".txt": parse_text,
    ".md": parse_text,
    ".pdf": parse_pdf,
    ".docx": parse_docx,
    ".xlsx": parse_xlsx,
    ".html": parse_html,
    ".htm": parse_html,
    ".png": parse_image,
    ".jpg": parse_image,
    ".jpeg": parse_image,
    ".tif": parse_image,
    ".tiff": parse_image,
}


def discover_documents(content_root: Path) -> Iterable[Path]:
    for path in sorted(content_root.rglob("*")):
        if path.is_file() and path.suffix.lower() in PARSERS:
            yield path


def parse_document(path: Path) -> ParsedDocument:
    parser = PARSERS.get(path.suffix.lower())
    if parser is None:
        raise ValueError(f"Unsupported file extension: {path.suffix}")
    return parser(path)
