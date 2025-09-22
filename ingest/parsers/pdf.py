"""PDF parsing including OCR fallback."""

from __future__ import annotations

import importlib
import io
from collections.abc import Iterable
from pathlib import Path
from typing import Any, cast

import fitz
from PIL import Image

from ..models import ParsedDocument, ParsedSection

pytesseract: Any | None
camelot: Any | None
tabula: Any | None

try:  # pragma: no cover - optional dependency
    pytesseract = importlib.import_module("pytesseract")
except Exception:  # pragma: no cover - runtime fallback
    pytesseract = None

try:  # pragma: no cover - optional dependency
    camelot = importlib.import_module("camelot")
except Exception:  # pragma: no cover
    camelot = None

try:  # pragma: no cover - optional dependency
    tabula = importlib.import_module("tabula")
except Exception:  # pragma: no cover
    tabula = None


def _extract_ocr(page: fitz.Page) -> str:
    if pytesseract is None:  # pragma: no cover - optional binary
        return ""
    try:
        pix = page.get_pixmap()
        buffer = io.BytesIO(pix.tobytes("png"))
        with Image.open(buffer) as image:
            return cast(str, pytesseract.image_to_string(image))
    except Exception:
        # If OCR tooling is unavailable at runtime, fall back silently
        return ""


def parse_pdf(path: Path) -> ParsedDocument:
    document = fitz.open(str(path))
    sections: list[ParsedSection] = []
    for index, page in enumerate(document, start=1):
        text = page.get_text("text")
        if not text.strip():
            text = _extract_ocr(page)
        breadcrumbs = [f"Page {index}"]
        sections.append(
            ParsedSection(text=text.strip(), page_number=index, breadcrumbs=breadcrumbs)
        )
    document.close()

    table_sections = list(_extract_tables(path))
    sections.extend(table_sections)

    return ParsedDocument(
        source_path=path,
        source_type="pdf",
        sections=sections,
    )


def _extract_tables(path: Path) -> Iterable[ParsedSection]:  # noqa: PLR0912
    tables_found = False
    if camelot is not None:  # pragma: no cover - requires camelot dependencies
        try:
            tables = camelot.read_pdf(str(path), pages="all")
        except Exception:
            tables = []
        for index, table in enumerate(tables, start=1):
            dataframe = getattr(table, "df", None)
            if dataframe is None:
                continue
            if dataframe.empty:
                continue
            tables_found = True
            cleaned = dataframe.fillna("")
            header = [str(cell).strip() for cell in cleaned.iloc[0].tolist()]
            rows = cleaned.iloc[1:]
            lines = [
                " | ".join(str(cell).strip() for cell in row.tolist()) for _, row in rows.iterrows()
            ]
            content = "\n".join(lines)
            if not content.strip():
                continue
            extra = {
                "is_table": "true",
                "table_headers": ", ".join(header),
            }
            page_number = getattr(table, "page", None)
            breadcrumbs = [f"Table {index}"]
            if page_number:
                extra["page_number"] = str(page_number)
                breadcrumbs.append(f"Page {page_number}")
            yield ParsedSection(
                text=content,
                page_number=int(page_number) if isinstance(page_number, int) else None,
                heading=f"Table {index}",
                extra=extra,
                breadcrumbs=breadcrumbs,
            )
    if tables_found:
        return

    if tabula is not None:  # pragma: no cover - requires java
        try:
            dataframes = tabula.read_pdf(str(path), pages="all", multiple_tables=True)
        except Exception:
            dataframes = []
        for index, dataframe in enumerate(dataframes, start=1):
            if dataframe is None or dataframe.empty:
                continue
            cleaned = dataframe.fillna("")
            header = [str(col).strip() for col in cleaned.columns]
            lines = [" | ".join(str(value).strip() for value in row) for row in cleaned.to_numpy()]
            content = "\n".join(lines)
            if not content.strip():
                continue
            extra = {
                "is_table": "true",
                "table_headers": ", ".join(header),
            }
            breadcrumbs = [f"Table {index}"]
            yield ParsedSection(
                text=content,
                heading=f"Table {index}",
                extra=extra,
                breadcrumbs=breadcrumbs,
            )
