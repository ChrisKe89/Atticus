# Atticus

Atticus is a Retrieval-Augmented Generation (RAG) pipeline focused on FUJIFILM multifunction device knowledge. It applies the
content taxonomy, ingestion controls, evaluation gates, and observability guidance defined in `AGENTS.md`.

## Platform Summary

- **Runtime:** Python 3.12
- **LLM:** `gpt-4.1`
- **Embedding model:** `text-embedding-3-large` (deterministic fallback used when no OpenAI key is present)
- **Content taxonomy:** see `content/` or `docs/README.md` for placement rules (§3.1)

## Quick Start (Docker Compose)

1. Copy `.env.example` to `.env` and set your OpenAI credentials. The `.env` file now includes chunking controls (`CHUNK_TARGET_TOKENS`, `CHUNK_MIN_TOKENS`, `CHUNK_OVERLAP_TOKENS`) that default to the values defined in `config.yaml`.
2. Review `config.yaml` for directory locations, model pins, and evaluation thresholds. All services load this file via `atticus.config.load_settings()`.
3. Build and launch the stack:

   ```bash
   make up
   ```

   This runs the FastAPI app on port `8000` behind Nginx (`80/443`).
4. Tail service logs as needed with `make logs` and stop the stack with `make down`.

The compose file mounts `content/`, `indices/`, and `logs/` so local changes persist across container rebuilds.

## Local Environment Setup (No Make)

Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

macOS/Linux

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Then build the index and run a smoke eval:

```bash
python scripts/ingest.py
python scripts/eval_run.py --json
```

Start the API locally:

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Helpful development shortcuts (if GNU Make is available):

- `make dev` - runs `uvicorn` with autoreload.
- `make lint`, `make typecheck`, `make test`, or `make check` - run the individual or combined quality gates.
- `make compile` - regenerate `requirements.txt` from `requirements.in` using `pip-compile`.
- `dev.http` - ready-to-run HTTPie/VS Code REST Client snippets for `/health`, `/ask`, `/ingest`, `/eval/run`, and admin endpoints.

## Testing & Quality

- Unit tests: `pytest -q`
- Coverage (target ≥90%): `pytest --cov --cov-report=term-missing`
- Lint: `ruff check .`
- Type check: `mypy`

## API Documentation

- Generate the OpenAPI schema locally:

  ```bash
  python scripts/generate_api_docs.py --output docs/api/openapi.json
  ```

- Pass `--format yaml` for a YAML export or adjust `--output` to point at a different file. The command loads `api.main.app` directly; the server does not need to be running.
- The resulting artifacts live under `docs/api/` alongside usage notes.

## Ingestion Workflow (§3)

1. Place new or updated documents under `content/` following the taxonomy in §3.1.
2. Run the ingestion pipeline:

   ```bash
   make ingest  # or: python scripts/ingest.py --paths <optional subset>
   ```

   The CLI reads the same `config.yaml` defaults and supports `--full-refresh`, `--paths`, and `--output` arguments for automation.
3. Inspect `logs/app.jsonl` for the `ingestion_complete` event. A manifest, FAISS index, and snapshot are written under `indices/`. Reused chunks retain their metadata (model version, breadcrumbs, token spans).

## Retrieval, Admin, and Observability

- The vector store implementation lives in `retriever/vector_store.py` and powers `/ask` queries with hybrid re-ranking.
- Structured JSON logs are emitted to `logs/app.jsonl`. Aggregated rollups are flushed to `logs/metrics/metrics.csv` via `atticus.metrics.MetricsRecorder`.
- Admin endpoints include `/admin/dictionary`, `/admin/errors`, and `/admin/sessions`. Use `/admin/sessions?format=html` for an HTML dashboard of recent requests (confidence, latency, escalation flag, and filters).

## Evaluation Runbook (§4)

1. Ensure the latest index is on disk (run ingestion first if required).
2. Execute the evaluation harness:

   ```bash
   make eval  # or: python scripts/eval_run.py --json --output-dir eval/runs/manual
   ```

   The CLI exits non-zero if any metric regresses beyond the configured threshold (`EVAL_REGRESSION_THRESHOLD`).
3. Metrics (`metrics.csv`) and per-query summaries (`summary.json`) are stored under `eval/runs/YYYYMMDD/`.
4. Compare results against `eval/baseline.json`; releases fail if any metric regresses by more than **3%** (enforced in CI).

## Release Checklist (§8)

1. Ingest new content and capture the updated manifest/index snapshot in `indices/snapshots/`.
2. Run the evaluation harness and confirm metrics stay within the 3% regression guardrail.
3. Update `CHANGELOG.md` and this `README.md` with notable changes and evaluation deltas.
4. Tag the repo using Semantic Versioning (e.g., `v0.1.0`) and include evaluation notes in the tag message.

## CED Chunking Pipeline

The dedicated CED workflow converts structured device collateral into JSONL artifacts for downstream indexing. Example:

```bash
python scripts/chunk_ced.py \
  --input content/model/AC7070/Apeos_C7070-C6570-C5570-C4570-C3570-C3070-C2570-CSO-FN-CED-362.pdf \
  --output data/index/ced-362.chunks.jsonl \
  --tables data/index/ced-362.tables.jsonl \
  --doc-index data/index/ced-362.doc_index.json
```

The CLI respects the chunking defaults from `config.yaml` and enriches each chunk with metadata such as breadcrumbs, token indices, model coverage, keywords, and SHA-256 hashes. The source PDF is not stored in the repository; see `REQUIREMENTS.md#ced-362-source` for fulfilment details.

## Continuous Integration & Release Automation

- `.github/workflows/lint-test.yml` – runs Ruff, MyPy, and Pytest on pushes and pull requests.
- `.github/workflows/eval-gate.yml` – runs `scripts/eval_run.py` and uploads `eval/runs/ci/` artifacts; the job fails if metrics regress beyond the 3% guardrail.
- `.github/workflows/release.yml` – runs the full quality gate on tagged builds and publishes evaluation artifacts to the GitHub Release.

## Rollback Guidance (§7)

Detailed rollback steps (restoring the prior tag, index snapshot, and smoke tests) are documented in `scripts/rollback.md`. The CLI `python scripts/rollback.py --snapshot <dir>` supports optional smoke tests (`--limit`) and alternate config files (`--config`).

## Windows Notes (Ghostscript & Tesseract)

Some ingestion features rely on Ghostscript (for Camelot) and the UB Mannheim Tesseract build. On Windows:

1. Install Ghostscript from <https://ghostscript.com/releases/> and add the install directory (e.g., `C:\Program Files\gs\gs10.03.0\bin`) to the `PATH` environment variable.
2. Install the UB Mannheim Tesseract build from <https://github.com/UB-Mannheim/tesseract/wiki>. During setup, allow the installer to append its `tesseract.exe` location to `PATH`.
3. Restart your shell after modifying `PATH`, then verify availability:

   ```powershell
   tesseract --version
   gswin64c --version
   ```

If either command is missing, relaunch the terminal as an administrator and re-check the environment variables. Documented steps apply equally to Git Bash and PowerShell sessions.

## Release Notes (This Version)

- Baseline corpus ingested via `scripts/ingest.py`; 4 chunks reused and manifest/index snapshot stored (see `logs/ingest_summary.json`).
- Added CODEX operator prompt, API schema generator (`scripts/generate_api_docs.py` with `docs/api/openapi.json`), and `dev.http` request samples alongside Windows Ghostscript/Tesseract guidance.
- Evaluation run (2025-09-21) achieved **nDCG@10 = 0.55**, **Recall@50 = 0.60**, **MRR = 0.5333** with artifacts under `eval/runs/20250921/`.
