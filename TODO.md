# TODO — Atticus + CED

> Scope: deliver a **fully working** RAG agent using OpenAI (`text-embedding-3-large`, `gpt-4.1`) with Dockerized FastAPI + Nginx reverse proxy, evaluation harness, and observability — **without** Azure AD/SSO in the current release. Any existing Azure auth/code paths must be removed or disabled now and tracked as future work.

---

## 0) Guiding Principles
- [ ] **Single-node, containerized stack** (Docker Compose) with minimal dependencies.
- [ ] **No Azure auth now**; move all Azure-AD/SSO to future-state (see §14).
- [ ] **Python 3.12** across runtime, CI, and local dev.
- [ ] **OpenAI defaults pinned**: `text-embedding-3-large` + `gpt-4.1`.
- [ ] Reproducible builds; everything runnable via `make` or `doit` tasks.

---

## 1) Repo Bootstrap & Hygiene
- [ ] Create base structure:
```
atticus/
  api/
  ingest/
  retriever/
  eval/
  scripts/
  nginx/
  content/
    model/AC7070/
    model/generic/
    software/Papercut/
    service/
  docs/
  logs/
  .github/workflows/
```
- [ ] Add **.editorconfig**, **.gitattributes**, **.gitignore** (Python, VS Code, OS cruft).
- [ ] Add **.vscode** settings (format on save, Python 3.12, markdownlint rules).
- [ ] Add **pre-commit** with `ruff`, `mypy`, `black` (or `ruff format`), `markdownlint-cli2`.

---

## 2) Dependency & Environment Management
- [ ] Choose **uv** or **poetry** (or `pip-tools`) for locked deps.
- [ ] Pin core libs: `fastapi`, `uvicorn[standard]`, `pydantic`, `httpx`, `python-dotenv`, `pydantic-settings`.
- [ ] Parsing/OCR: `pymupdf`, `pdfminer.six`, `pytesseract`, `Pillow`.
- [ ] Table extraction (optional): `camelot-py` (needs Ghostscript) or `tabula-py` (Java).
- [ ] Embeddings/Retrieval: `faiss-cpu`, `numpy`, `scikit-learn` (optional), `rapidfuzz` (optional hybrid scoring).
- [ ] Testing: `pytest`, `pytest-cov`.
- [ ] Lint/type: `ruff`, `mypy`.

---

## 3) Dockerization
_No active items — completed 2025-09-21 (see `ToDo-Complete.md`)._

---

## 4) Nginx Reverse Proxy (Current Release, No Azure Auth)
_No active items — completed 2025-09-21 (see `ToDo-Complete.md`)._

---

## 5) API Surface (FastAPI)
- [ ] Implement endpoints: `/health`, `/ingest`, `/ask`, `/eval/run`, `/admin/dictionary`.
- [ ] Add middleware: request ID, structured JSON logging, timing, error handling.
- [ ] Define Pydantic models for requests/responses; enable OpenAPI.

---

## 6) Ingestion Pipeline
- [ ] Build parsers for **PDF, DOCX, XLSX (Q/A), HTML**.
- [ ] OCR via **Tesseract** (UB Mannheim build); auto-detect scanned PDFs.
- [ ] Table extraction: prefer Camelot; fallback Tabula.
- [ ] Chunking: ~512 tokens, ~20% overlap; keep breadcrumbs (file → section → page).
- [ ] Embedding: **OpenAI `text-embedding-3-large`**; metadata includes source, page, section, timestamp, model version.
- [ ] Indexing: **FAISS-flat** (on-disk).
- [ ] Manifest: `indices/manifest.json` with embedding model/version and corpus hash.
- [ ] CLI `scripts/ingest.py` to reprocess changed files.

---

## 7) Retrieval
- [ ] Vector top-K with metadata filters.
- [ ] Optional hybrid re-rank (BM25-lite).
- [ ] Return citations (filepath + page).

---

## 8) Generation
- [ ] Prompt template: concise answer + bullet citations; say “I don’t know” if not grounded.
- [ ] Model: **OpenAI `gpt-4.1`**, temperature ~0.2.
- [ ] Confidence scoring = vector similarity + LLM self-check.
- [ ] Escalation if **<70%** confidence or 3 clarifications.

---

## 9) Evaluation Harness
- [ ] Gold set at `eval/gold_set.csv` (question, answer, source, page).
- [ ] Harness in `eval/harness/test_eval.py` with **nDCG@10, Recall@50, MRR**.
- [ ] CI gate: fail if >3% regression.
- [ ] Store eval outputs under `eval/runs/YYYYMMDD/`.

---

## 10) Config & Secrets
- [ ] Central `config.yaml`.
- [ ] `.env` for secrets.

Example:
```
OPENAI_API_KEY=your_key_here
EMBED_MODEL=text-embedding-3-large
GEN_MODEL=gpt-4.1
CONFIDENCE_THRESHOLD=0.70
MAX_CONTEXT_CHUNKS=10
LOG_LEVEL=INFO
```

---

## 11) Observability
- [ ] JSON logs to `logs/app.jsonl`.
- [ ] Log schema: request_id, route, timings, top_k, confidence, status, error.
- [ ] CSV metrics: queries/day, avg confidence, escalations.
- [ ] Hook Prometheus (future).

---

## 12) CI/CD
- [ ] GitHub Actions: lint-test, build, eval-gate, release.

---

## 13) Documentation
- [ ] AGENTS.md, README.md, CODEX_PROMPT.md, CHANGELOG.md (auto).
- [ ] API docs auto-generated.

---

## 14) Azure Auth Removal
- [ ] Strip all Azure AD/SSO code/deps.
- [ ] Abstract auth for future use.
- [ ] Track migration in README.

---

## 15) Admin Tools
- [ ] Dictionary editor endpoints.
- [ ] Session log viewer (JSON/HTML).
- [ ] Error triage API.

---

## 16) Rollback & Snapshots
- [ ] Snapshot `indices/` per release.
- [ ] `scripts/rollback.py`.
- [ ] Smoke-test gold queries after rollback.

---

## 17) Seed Artifacts
- [ ] Gold_set.csv with 10 starter rows.
- [ ] Example files under `content/`.
- [ ] Postman/httpie samples.

---

## 18) Local Dev
- [ ] `dev.http` with sample requests.
- [ ] `make dev` alias for uvicorn reload.
- [ ] Windows install notes for Ghostscript/Tesseract.

---

## 19) Future-State
- [ ] Azure AD/SSO for Admin UI.
- [ ] pgvector/Postgres backend.
- [ ] Prometheus/Grafana at cluster scope.

---

## 20) Acceptance Criteria
- [ ] `docker compose up` → api + nginx healthy.
- [ ] `/ingest` indexes sample.
- [ ] `/ask` returns grounded answers + citations.
- [ ] `/eval/run` outputs metrics CSV.
- [ ] Logs structured.
- [ ] CI enforced; release tags with eval summary.

---

# TODO — CED Chunking & Eval

## Retrieval & Indexing
- [ ] **Implement CED chunking pipeline**
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
python scripts/chunk_ced.py   --input content/model/AC7070/Apeos_C7070-C6570-C5570-C4570-C3570-C3070-C2570-CSO-FN-CED-362.pdf   --output data/index/ced-362.chunks.jsonl   --tables data/index/ced-362.tables.jsonl   --doc-index data/index/ced-362.doc_index.json   --target-tokens 800 --min-tokens 400 --overlap 120
```

---

## Evaluation & Monitoring
- [ ] **Generate 10 simple eval Q/As CSV**
  - File: `eval/ced-362-smoke.csv`
  - Two columns: `Question,Answer`
  - Must contain exactly 10 rows (see spec).

**Command (Codex):**
```bash
cat > eval/ced-362-smoke.csv <<'EOF'
Question,Answer
"What is the maximum standard print resolution listed for these Apeos models?","Up to 1,200 × 2,400 dpi."
"What is the recommended maximum AMPV for the C7070?","50K impressions per month."
"What is the recommended minimum AMPV for the C2570?","6K impressions per month."
"Which page size enables long paper/banner printing via the Bypass Tray?","Up to 320 × 1200 mm (printable area 305 × 1194 mm)."
"Which PDLs are supported by default for printing?","PCL5 / PCL6 (PostScript optional)."
"What scan resolutions are available?","600×600, 400×400, 300×300, 200×200 dpi."
"What is the system memory listed for the devices?","4 GB (shared)."
"What is the capacity of the optional HCF B2?","2,940 sheets (80 gsm)."
"How many sheets can the Side Tray hold?","100 sheets (up to SRA3, 52–300 gsm)."
"What is the rated print speed (A4 LEF) for the C5570 in ppm (BW/Colour)?","55/55 ppm."
EOF
```

---

## Tooling & Config
- [ ] Codex task “Chunk CED PDFs → JSONL” using the above command.
- [ ] Codex task “Build CED smoke eval CSV (10)” using the above command.
- [ ] Pin embedding model `text-embedding-3-large@<pinned-version>`; reuse tokenizer.
- [ ] ENV vars: `CONFIDENCE_THRESHOLD`, `EMBEDDING_MODEL_VERSION`, `CHUNK_TARGET_TOKENS`, `CHUNK_MIN_TOKENS`, `CHUNK_OVERLAP_TOKENS`.
