# TODO — Atticus + CED

> Scope: deliver a **fully working** RAG agent using OpenAI (`text-embedding-3-large`, `gpt-4.1`) with Dockerized FastAPI + Nginx reverse proxy, evaluation harness, and observability — **without** Azure AD/SSO in the current release. Any existing Azure auth/code paths must be removed or disabled now and tracked as future work.

---

## 19) Future-State
- [ ] Azure AD/SSO for Admin UI.
  - Blocked: see REQUIREMENTS.md#future-state-roadmap.
- [ ] pgvector/Postgres backend.
  - Blocked: see REQUIREMENTS.md#future-state-roadmap.
- [ ] Prometheus/Grafana at cluster scope.
  - Blocked: see REQUIREMENTS.md#future-state-roadmap.

---

# TODO — CED Chunking & Eval

## Retrieval & Indexing
- [ ] **Implement CED chunking pipeline**
  - Blocked: see REQUIREMENTS.md#ced-362-source.
  - Chunk size: 800 tokens (target), min 400, overlap 120.
  - Heading-first segmentation; tables = own chunks.
  - Metadata required: `source_file, doc_type, ced_id, version, page_range, section_titles, breadcrumbs, is_table, table_headers, models, token_index, embedding_model, ingested_at, hash, models_present, keywords`.
  - Context summaries + breadcrumbs per chunk.
  - Reject poor OCR (>5% garble) or incomplete tables (>20% empty).
  - Outputs:
    - `data/index/ced-362.chunks.jsonl`
    - `data/index/ced-362.tables.jsonl`
    - `data/index/ced-362.doc_index.json`

**Command (Codex):**
```bash
python scripts/chunk_ced.py \
  --input content/model/AC7070/Apeos_C7070-C6570-C5570-C4570-C3570-C3070-C2570-CSO-FN-CED-362.pdf \
  --output data/index/ced-362.chunks.jsonl \
  --tables data/index/ced-362.tables.jsonl \
  --doc-index data/index/ced-362.doc_index.json \
  --target-tokens 800 --min-tokens 400 --overlap 120
```

---

## Tooling & Config
- [ ] Codex task “Chunk CED PDFs → JSONL” using the above command.
  - Blocked: see REQUIREMENTS.md#ced-362-source.

