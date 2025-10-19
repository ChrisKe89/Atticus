from collections import OrderedDict
from types import SimpleNamespace

from atticus.vector_db import StoredChunk
from retriever.vector_store import RetrievalMode, SearchResult, VectorStore


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
    vs.settings = SimpleNamespace(
        pgvector_probes=4,
        pgvector_lists=16,
        embed_model="text-embedding-3-large",
    )
    vs.logger = SimpleNamespace()
    vs.repository = SimpleNamespace()
    vs.manifest = SimpleNamespace(
        documents=manifest_overrides or {"content/model/manual.pdf": {"source_type": "ced"}}
    )
    vs._cache_limit = 10
    vs._query_cache = OrderedDict()
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


def test_query_cache_returns_clones():
    vs = _make_vector_store()
    result = SearchResult(
        chunk_id="chunk-1",
        source_path="content/model/manual.pdf",
        text="Example chunk text.",
        score=0.5,
        page_number=1,
        heading="Overview",
        metadata={"source_type": "ced"},
        chunk_index=0,
        vector_score=0.4,
        lexical_score=0.2,
        fuzz_score=0.1,
    )
    vs._cache_store("cache-key", [result])
    cached = vs._cache_get("cache-key")
    assert cached is not None
    assert cached[0] is not result
    assert cached[0].metadata is not result.metadata


def test_resolve_probes_scales_with_query():
    vs = _make_vector_store()
    short = vs._resolve_probes(RetrievalMode.HYBRID, top_k=20, query="dpi specs")
    long_query = " ".join(["specification"] * 20)
    long = vs._resolve_probes(RetrievalMode.HYBRID, top_k=5, query=long_query)
    assert short > vs.settings.pgvector_probes
    assert long >= vs.settings.pgvector_probes
