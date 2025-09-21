# Atticus

Atticus is a Retrieval-Augmented Generation (RAG) pipeline focused on FUJIFILM multifunction device knowledge. It applies the
content taxonomy, ingestion controls, evaluation gates, and observability guidance defined in `AGENTS.md`.

## Platform Summary
- **Runtime:** Python 3.12
- **LLM:** `gpt-4.1`
- **Embedding model:** `text-embedding-3-large` (deterministic fallback used when no OpenAI key is present)
- **Content taxonomy:** see `content/` or `docs/README.md` for placement rules (§3.1)

## Quick Start (Docker Compose)
1. Copy `.env.example` to `.env` and set your OpenAI credentials and tuning parameters.
2. Build and launch the stack:
   ```bash
   make up
   ```
   This runs the FastAPI app on port `8000` behind Nginx (`80/443`).
3. Tail service logs as needed with `make logs` and stop the stack with `make down`.

The compose file mounts `content/`, `indices/`, and `logs/` so local changes persist across container rebuilds.

## Local Environment Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Ingestion Workflow (§3)
1. Place new or updated documents under `content/` following the taxonomy in §3.1.
2. Run the ingestion pipeline:
   ```bash
   make ingest  # or: python scripts/run_ingestion.py
   ```
3. Inspect `logs/app.jsonl` for the `ingestion_complete` event. A manifest, FAISS index, and snapshot are written under `indices/`.

## Retrieval & Observability
- The vector store implementation lives in `retriever/vector_store.py` and powers `/ask` queries.
- Structured JSON logs are emitted to `logs/app.jsonl`. Additional counters are written via `atticus/metrics.py`.

## Evaluation Runbook (§4)
1. Ensure the latest index is on disk (run ingestion first if required).
2. Execute the evaluation harness:
   ```bash
   make eval  # or: python -m eval.runner
   ```
3. Metrics and per-query breakdowns are stored under `eval/runs/YYYYMMDD/`.
4. Compare results against `eval/baseline.json`; releases fail if any metric regresses by more than **3%**.

## Release Checklist (§8)
1. Ingest new content and capture the updated manifest/index snapshot in `indices/snapshots/`.
2. Run the evaluation harness and confirm metrics stay within the 3% regression guardrail.
3. Update `CHANGELOG.md` and this `README.md` with notable changes and evaluation deltas.
4. Tag the repo using Semantic Versioning (e.g., `v0.1.0`) and include evaluation notes in the tag message.

## Rollback Guidance (§7)
Detailed rollback steps (restoring the prior tag, index snapshot, and smoke tests) are documented in `scripts/rollback.md`.
