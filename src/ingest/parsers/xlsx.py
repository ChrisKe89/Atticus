"""Parser for XLSX question and answer sheets."""

from __future__ import annotations

from pathlib import Path

from openpyxl import load_workbook

from ..models import ParsedDocument, ParsedSection

EXPECTED_COLUMNS = {"question", "answer"}


def parse_xlsx(path: Path) -> ParsedDocument:
    workbook = load_workbook(str(path), data_only=True)
    sheet = workbook.active
    try:
        header_row = next(sheet.iter_rows(min_row=1, max_row=1))
    except StopIteration:
        header_row = []
    headers = [cell.value for cell in header_row]
    normalized = [str(header).strip().lower() for header in headers if header is not None]

    column_map = {name: normalized.index(name) for name in EXPECTED_COLUMNS if name in normalized}
    sections: list[ParsedSection] = []

    for row in sheet.iter_rows(min_row=2):
        cells = [cell.value for cell in row]
        if not any(cells):
            continue
        question = str(cells[column_map["question"]]).strip() if "question" in column_map else ""
        answer = str(cells[column_map["answer"]]).strip() if "answer" in column_map else ""
        if not question and not answer:
            continue
        source = ""
        if "source" in normalized:
            source_idx = normalized.index("source")
            source = str(cells[source_idx]).strip() if cells[source_idx] else ""
        page = None
        if "page" in normalized:
            page_idx = normalized.index("page")
            value = cells[page_idx]
            try:
                page = int(value) if value is not None else None
            except (TypeError, ValueError):
                page = None
        text = f"Q: {question}\nA: {answer}"
        extra = {}
        if source:
            extra["source"] = source
        breadcrumbs = ["Q&A"]
        section = ParsedSection(text=text, page_number=page, extra=extra, breadcrumbs=breadcrumbs)
        sections.append(section)

    return ParsedDocument(
        source_path=path,
        source_type="xlsx",
        sections=sections,
    )
