# Atticus

Atticus is a Retrieval-Augmented Generation (RAG) pipeline focused on FUJIFILM multifunction device knowledge. It applies the
content taxonomy, ingestion controls, evaluation gates, and observability guidance defined in `AGENTS.md`.

## Platform Summary
- **Runtime:** Python 3.12
- **LLM:** `gpt-4.1`
- **Embedding model:** `text-embedding-3-large` (deterministic fallback used when no OpenAI key is present)
- **Content taxonomy:** see `content/` or `docs/README.md` for placement rules (§3.1)

## Environment Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install numpy openai pytest
```

## Ingestion Workflow (§3)
1. Add or update source files under `content/` using the taxonomy in §3.1.
2. Run `python scripts/run_ingestion.py` to parse, chunk (~512 tokens with ~20% overlap), embed, and persist the index.
3. Review the structured JSON log in `logs/app.jsonl` for the `ingestion_complete` event and snapshot path.
4. Commit the updated `indexes/atticus_index.json` and the new `indexes/snapshots/*.json` snapshot.

## Retrieval & Observability
- Retrieval helpers live in `atticus/retrieval.py`; they perform cosine search over the persisted vectors.
- JSON logs rotate via `logs/app.jsonl`. Additional usage metrics can be emitted with `MetricsRecorder` in
  `atticus/observability/metrics.py` (records queries/day, average confidence, escalations/day, latency).

## Evaluation Runbook (§4)
1. Ensure the latest index is committed.
2. Execute `pytest evaluation/harness` to regenerate metrics and artifacts.
3. Results are written under `evaluation/runs/YYYYMMDD/<timestamp>/` as `metrics.csv` and `summary.json`.
4. The pytest harness fails if nDCG@10, Recall@50, or MRR regress by more than **3%** versus `evaluation/baseline/metrics.json`.

### Latest Evaluation (2025-09-20)
| Metric    | Score | Δ vs. baseline |
|-----------|-------|----------------|
| nDCG@10   | 1.00  | +0.00          |
| Recall@50 | 1.00  | +0.00          |
| MRR       | 1.00  | +0.00          |

Artifacts: `evaluation/runs/20250920/235132/`

## Release Checklist (§8)
1. Ingest new/updated content and commit the index snapshot.
2. Run the evaluation harness and confirm metrics stay within the 3% regression guardrail.
3. Update `CHANGELOG.md` and this `README.md` with model versions, content highlights, and evaluation deltas.
4. Tag the repo using Semantic Versioning (e.g., `v0.1.0`) and include evaluation notes in the tag message.

## Rollback Guidance (§7)
Detailed rollback steps (restoring the prior tag, index snapshot, and smoke tests) are documented in `scripts/rollback.md`.
