# Atticus — Agents & System Design (Updated)

> Single‑service RAG stack that ingests FUJIFILM documents, builds a local FAISS index, retrieves, and answers with sources. Defaults to **OpenAI `text-embedding-3-large`** for embeddings and **`gpt-4.1`** for generation. Python 3.12.

## 1) Purpose & Scope
Atticus is a pragmatic, production‑lean RAG service. It must:
- Parse & chunk PDFs/Office/HTML/Images and XLSX Q&A sheets
- Embed + index in FAISS, snapshotting metadata and a manifest
- Serve an `/ask` API that returns answer, citations, confidence, and a `should_escalate` flag
- Evaluate retrieval quality (nDCG@10, Recall@50, MRR) on a gold set with regression checks
- Run without Docker if needed (local venv is fine); Docker/Nginx are provided for deployment

## 2) Architecture (High‑level)
- **Parsers**: `pdf.py`, `docx.py`, `html.py`, `image.py`, `text.py`, `xlsx.py`
- **Chunking**: `chunker.py` creates token‑bounded overlapping chunks with breadcrumb metadata
- **Ingestion**: `pipeline.py` discovers new/changed docs, reuses existing chunks by SHA‑256, embeds, builds FAISS, writes metadata, snapshots, and updates a manifest
- **Vector search**: `vector_store.py` (FAISS), hybrid mode optional
- **Generation**: `generator.py` builds the answer from top K chunks using OpenAI; a local summarizer acts as a fallback
- **Service API**: `service.py` / FastAPI app exposes `/ask`, `/ingest`, `/eval/run`, `/health`, plus admin endpoints
- **Evaluation**: `eval_qa.py` / `runner.py` compute metrics and compare to a JSON baseline
- **UI**: `index.html`/`styles.css`/`main.js` demo client

### Data flow (ingestion)
1. Parse files → `ParsedDocument` with `ParsedSection`s
2. Chunk → `Chunk` with token spans, page numbers, breadcrumbs
3. Embed new chunks; reuse previous chunk embeddings if unchanged
4. Build FAISS + metadata; write snapshot + manifest; log event

## 3) Config & Environment
Environment variables (read via settings):
- `OPENAI_API_KEY` — required for online generation/embeddings
- `EMBED_MODEL` (default: `text-embedding-3-large`)
- `EMBED_DIM` (default: 3072)
- `CHUNK_TARGET_TOKENS` (default from config)
- `CHUNK_OVERLAP_TOKENS` (default from config)
- `CONFIDENCE_THRESHOLD` (default: 0.7) — values < threshold set `should_escalate=true`
- Paths: `CONTENT_DIR`, `INDICES_DIR`, `LOGS_DIR`, `EVAL_DIR` (override as needed)

Configuration files:
- `manifest.json` — corpus hash, counts, model versions, paths
- `index_metadata.json` — stored chunk metadata
- `baseline.json` — target retrieval metrics to avoid regressions

## 4) Fallback & Error Modes
- If `OPENAI_API_KEY` is **unset** or an API error occurs, Atticus uses a **local summarizer** over retrieved chunks. This is meant for diagnosis only and will usually reduce confidence.
- When fallback fires, the service sets `should_escalate=true` if `confidence < CONFIDENCE_THRESHOLD` and logs the event with details for triage.
- The fallback can be disabled at runtime with `--no-fallback` in developer scripts (or a settings flag) if strict failures are preferred.

## 5) Ingestion & Chunking (Details)
- **Chunking**: tokenise section text; split at `CHUNK_TARGET_TOKENS` with `CHUNK_OVERLAP_TOKENS`; ensure small trailing chunks are merged; enrich metadata with breadcrumbs, page numbers, section headings, and source type.
- **Dedup & reuse**: if a file’s SHA‑256 matches the manifest, reuse existing chunk embeddings (zero‑cost) and skip re‑embedding.
- **Snapshots**: every ingest creates a time‑stamped snapshot under `indices/snapshots/<timestamp>/` for rollback.

## 6) Retrieval & Answering
- Retrieve top‑K by vector similarity (hybrid retrieval optional if BM25 is configured).
- Compose an answer with in‑text citations; score confidence from retrieval scores and heuristic signals.
- If `confidence < CONFIDENCE_THRESHOLD` (default 0.7), mark `should_escalate=true`.

## 7) API Endpoints (FastAPI)
- `POST /ask` → `{ answer, citations[], confidence, should_escalate, request_id }`
- `POST /ingest` → run ingestion with `{ full_refresh, paths[] }`
- `POST /eval/run` → compute metrics vs. baseline; emits CSV & JSON summaries
- `GET /health` → manifest presence, counts, model info
- `GET /admin/sessions?format=json|html` → recent requests (for ops)
- `GET /admin/errors?since=<iso>` → error log

## 8) Evaluation & Baselines
- Gold set CSV columns: `question,relevant_documents,expected_answer,notes` (semicolon‑separated docs).
- Metrics: **nDCG@10**, **Recall@50**, **MRR**. Results are written to an output folder (dated) as `metrics.csv` and `summary.json` and compared with `baseline.json`.
- CI can fail if deltas are negative beyond tolerance (e.g., –3% drop).

## 9) Deployment
- **Local**: create venv, install `requirements.txt`, run `uvicorn`.
- **Docker**: `Dockerfile` builds API; `nginx.conf` reverse‑proxies `/:80 → api:8000` with static UI served by Nginx.
- **No‑Docker path** is supported for constrained environments; keep `.env`/`config.yaml` consistent in both modes.

## 10) Release, Rollback & Versioning
- Tag releases after a green eval; commit `indices/manifest.json` and snapshot file.
- Rollback: deploy prior snapshot; restore `manifest.json` alongside to keep counts in sync.
- Maintain `CHANGELOG.md`; update `AGENTS.md` any time a new parser, retrieval option, or confidence policy changes.

## 11) Security Notes
- Keep model/API keys out of source; use environment variables or secrets management.
- Never serve raw content outside your allowed directories.
- Logs may include user questions; rotate and restrict access appropriately.

## 12) Known Limitations
- OCR quality depends on Tesseract; image‑heavy PDFs may require GPU OCR in future.
- Fallback summariser is intentionally conservative; it’s a diagnostic tool, not a product feature.
- If your gold set uses Windows paths, normalisation to POSIX is required for consistent evals across OSes.

---

### Quick‑Start Commands (Windows‑friendly)

```powershell
# 1) Setup
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -U pip
pip install -r requirements.txt

# 2) Ingest
$env:OPENAI_API_KEY="<your key>"    # or rely on .env
python run_ingestion.py

# 3) Smoke eval
python eval_run.py --json

# 4) Serve
uvicorn service:app --host 0.0.0.0 --port 8000

# 5) UI
# open http://localhost:8000/ui
```

### Notes for Contributors
- Keep Q&A XLSX columns strictly: `question`, `answer` (plus optional `source`, `page`).
- Prefer `YYYYMMDD_name_vN.ext` filenames for traceability.
- Update baseline after a *justified* improvement with a PR that includes methodology and diffs.
