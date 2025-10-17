from types import SimpleNamespace

from atticus.vector_db import StoredChunk
from retriever.vector_store import VectorStore


def _make_chunk(product_family: str) -> StoredChunk:
    chunk = StoredChunk(
        chunk_id="chunk-1",
        document_id="doc-1",
        source_path="content/model/manual.pdf",
        text="Example chunk text.",
        start_token=0,
        end_token=10,
        page_number=1,
        section="Overview",
        sha256="fake",
        extra={"product_family": product_family, "source_type": "ced"},
    )
    return chunk


def _make_vector_store(manifest_overrides: dict | None = None) -> VectorStore:
    vs: VectorStore = VectorStore.__new__(VectorStore)  # bypass __init__
    vs.settings = SimpleNamespace()
    vs.logger = SimpleNamespace()
    vs.repository = SimpleNamespace()
    vs.manifest = SimpleNamespace(
        documents=manifest_overrides or {"content/model/manual.pdf": {"source_type": "ced"}}
    )
    return vs


def test_apply_filters_allows_matching_family():
    vs = _make_vector_store()
    chunk = _make_chunk("C7070")
    assert vs._apply_filters(chunk, {"product_family": "C7070"})


def test_apply_filters_blocks_non_matching_family():
    vs = _make_vector_store()
    chunk = _make_chunk("C8180")
    assert not vs._apply_filters(chunk, {"product_family": "C7070"})


def test_apply_filters_passes_without_family_constraint():
    vs = _make_vector_store()
    chunk = _make_chunk("C7070")
    assert vs._apply_filters(chunk, {"path_prefix": "content"})
