# TODO — Atticus

> Scope: deliver a **fully working** RAG agent using OpenAI (`text-embedding-3-large`, `gpt-4.1`) with Dockerized FastAPI + Nginx reverse proxy, evaluation harness, and observability — **without** Azure AD/SSO in the current release. Any existing Azure auth/code paths must be removed or disabled now and tracked as future work.

---

## 0) Guiding Principles
- [ ] **Single-node, containerized stack** (Docker Compose) with minimal dependencies.
- [ ] **No Azure auth now**; move all Azure-AD/SSO to future-state (see §14). Keep storage residency policies intact.
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
- [ ] `GET /health` — liveliness probe.
- [ ] `POST /ingest` — ingest one or more files from `content/` or upload; returns counts and manifest deltas.
- [ ] `POST /ask` — body: `{query, k=10, filters?}` → returns `answer, citations[], confidence, timings`.
- [ ] `POST /eval/run` — runs eval harness against gold set; returns metrics; dumps CSV to `eval/runs/YYYYMMDD/`.
- [ ] `GET /admin/dictionary` + `POST /admin/dictionary` — manage synonyms.
- [ ] **Middleware**: request ID, structured JSON logging, timing, error handling.
- [ ] **Pydantic** models for requests/responses; OpenAPI enabled.

---

## 6) Ingestion Pipeline
- [ ] Parsers for **PDF, DOCX, XLSX (Q/A), HTML**.
- [ ] OCR via **Tesseract** (UB Mannheim build on Windows hosts); auto-detect scanned PDFs.
- [ ] Table extraction (prefer Camelot if Ghostscript present; fallback to Tabula); capture captions.
- [ ] Chunking: ~512 tokens, ~20% overlap; keep breadcrumbs (file → section → page).
- [ ] Embedding: **OpenAI `text-embedding-3-large`**; store vector + metadata (source path, page, section, timestamp, model version).
- [ ] Indexing: **FAISS-flat** (on-disk) with snapshotting under `indices/`.
- [ ] Manifest file `indices/manifest.json` including embedding model/version and corpus hash.
- [ ] CLI `scripts/ingest.py` to process either full corpus or changed files since last manifest.

---

## 7) Retrieval
- [ ] Vector top-K with metadata filters (folder, type, date).
- [ ] Optional hybrid re-rank: BM25-lite (rapidfuzz) on top of vector candidates.
- [ ] Citation packaging: return filepath + page numbers per chunk.

---

## 8) Generation
- [ ] Prompt template: concise answer + bullet citations; “say I don’t know” if not grounded.
- [ ] LLM: **OpenAI `gpt-4.1`**, temperature ~0.2 for factuality.
- [ ] Confidence scoring: combine (a) mean/max similarity of cited chunks and (b) LLM self-check scalar.
- [ ] Escalation rule: **<70%** confidence or 3 clarification attempts.

---

## 9) Evaluation Harness
- [ ] Gold set at `eval/gold_set.csv` (columns: question, answer, source, page(s)).
- [ ] Harness `eval/harness/test_eval.py` (pytest) computing **nDCG@10, Recall@50, MRR**.
- [ ] CI gate: fail if regression **>3%** vs `eval/baseline.json` (updated on successful release).
- [ ] Artifacts: CSV + JSON summary under `eval/runs/YYYYMMDD/`.

---

## 10) Config, Secrets, and Environment
- [ ] Central `config.yaml` (chunk size, overlap, k, thresholds).
- [ ] Environment variables via `.env` (never commit real secrets).

**.env.example**
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
- [ ] Structured JSON logs to `logs/app.jsonl` (rotate by size/date).
- [ ] Log schema: request_id, route, timings, top_k, confidence, status, error.
- [ ] Simple metrics aggregator writing CSV (queries/day, avg confidence, escalations).
- [ ] Hook for Prometheus (future-state, optional).

---

## 12) CI/CD (GitHub Actions)
- [ ] **lint-test.yml**: ruff, mypy, pytest.
- [ ] **build.yml**: build/push images (optional local only).
- [ ] **eval-gate.yml**: run eval; block merge on >3% regression.
- [ ] **release.yml**: on tag – attach eval summary to `CHANGELOG.md`, create GitHub Release.

---

## 13) Documentation
- [ ] **AGENTS.md** (already present) – ensure pinned models, rules, runbooks.
- [ ] **README.md** – quick start (Docker), ingestion, asking, evaluation, troubleshooting.
- [ ] **API docs** – auto-generated OpenAPI link and curl examples.
- [ ] **CODEX_PROMPT.md** – automation instructions.
- [ ] **CHANGELOG.md** – maintained by automation; human-readable highlights.

---

## 14) Azure Auth — Move to Future State (and Remove Now)
- [ ] **REMOVE** any Azure AD/SSO code paths, middleware, or dependencies from current build.
- [ ] **Search & strip**: references to MSAL, Entra ID, AD Graph, or Azure OAuth flows.
- [ ] **Abstract** auth interfaces to allow future drop-in (feature flag off by default).
- [ ] **TODO (future)**: Implement Azure AD/SSO behind feature flag, with role-based admin UI.
- [ ] **TODO (cleanup)**: Open ticket to track removal PR; add migration note in README.

---

## 15) Admin Tools
- [ ] Dictionary editor endpoints (`GET/POST /admin/dictionary`).
- [ ] Session log viewer (anonymized) – simple HTML or JSON export.
- [ ] Error triage endpoint (`GET /admin/errors?since=...`).

---

## 16) Rollback & Snapshots
- [ ] Snapshot `indices/` on each release; name `indices/vX.Y.Z/`.
- [ ] Script `scripts/rollback.py` to restore previous snapshot and config pins.
- [ ] Smoke tests: top-20 gold queries within 60s after rollback.

---

## 17) Seed Artifacts
- [ ] Template **gold_set.csv** with 10 starter Q/A rows (developer fills in).
- [ ] Example **content** files under each folder demonstrating naming conventions.
- [ ] Postman collection (optional) or `httpie` `.http` files for API calls.

---

## 18) Local Dev Quality-of-Life
- [ ] `dev.http` with sample requests.
- [ ] `make dev` alias to run API without Docker (uvicorn reload) for fast iteration.
- [ ] Windows notes for Ghostscript & Tesseract installs.

---

## 19) Future-State (Not in Current Release)
- [ ] Azure AD/SSO integration for Admin UI.
- [ ] pgvector/Postgres deployment for multi-user scaling.
- [ ] Prometheus/Grafana metrics at cluster scope.

---

## 20) Acceptance Criteria (Definition of Done)
- [ ] `docker compose up` brings **nginx** + **api** healthy.
- [ ] `POST /ingest` indexes example content; manifest and indices written.
- [ ] `POST /ask` returns grounded answer + citations with confidence score.
- [ ] `POST /eval/run` produces metrics and CSV under `eval/runs/DATE/`.
- [ ] Logs present in `logs/app.jsonl` with structured entries.
- [ ] CI gates enforced; release tag created with attached eval summary.
