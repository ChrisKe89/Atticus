from __future__ import annotations

from retriever.citation_utils import dedupe_citations


def test_dedupe_by_path_and_pages_simple_dicts() -> None:
    items = [
        {"source_path": "docs/Guide-A.pdf", "page_range": [10, 11]},
        {"source_path": "docs/Guide-A.pdf", "page_range": [10, 11]},
        {"source_path": "docs/Guide-A.pdf", "page_range": [12]},
        {"source_path": "docs/Guide-B.pdf", "page_range": [1]},
        {"source_path": "docs/guide-a.PDF", "page_range": [12]},
    ]
    out = dedupe_citations(items)
    assert len(out) == 3
    assert out[0]["page_range"] == [10, 11]
    assert out[1]["page_range"] == [12]
    assert out[2]["source_path"].endswith("Guide-B.pdf")


class Obj:
    def __init__(self, source_path: str, page_range: object) -> None:
        self.source_path = source_path
        self.page_range = page_range


def test_dedupe_supports_objects_and_sets_pages() -> None:
    items = [
        Obj("docs/Ref.pdf", {2, 3}),
        Obj("docs/Ref.pdf", [3, 2]),
        Obj("docs/Ref.pdf", (4,)),
    ]
    out = dedupe_citations(items)
    assert len(out) == 2
    assert isinstance(out[0], Obj)
