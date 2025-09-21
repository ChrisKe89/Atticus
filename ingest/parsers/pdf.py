"""PDF parsing including OCR fallback."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any, cast

import fitz  # type: ignore[import-untyped]
from PIL import Image

from ..models import ParsedDocument, ParsedSection

try:  # pragma: no cover - optional dependency
    import pytesseract as _pytesseract  # type: ignore[import-untyped]
except Exception:  # pragma: no cover - runtime fallback
    _pytesseract = None

pytesseract: Any | None = _pytesseract


def _extract_ocr(page: fitz.Page) -> str:
    if pytesseract is None:  # pragma: no cover - optional binary
        return ""
    pix = page.get_pixmap()
    buffer = io.BytesIO(pix.tobytes("png"))
    with Image.open(buffer) as image:
        return cast(str, pytesseract.image_to_string(image))


def parse_pdf(path: Path) -> ParsedDocument:
    document = fitz.open(str(path))
    sections: list[ParsedSection] = []
    for index, page in enumerate(document, start=1):
        text = page.get_text("text")
        if not text.strip():
            text = _extract_ocr(page)
        sections.append(ParsedSection(text=text.strip(), page_number=index))
    document.close()

    return ParsedDocument(
        source_path=path,
        source_type="pdf",
        sections=sections,
    )

