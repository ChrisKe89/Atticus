# Changelog

## [Unreleased]

## [0.2.0] - 2025-09-21
### Added
- Introduced `config.yaml`/`.env` harmony via `atticus.config.load_settings()` and new chunking environment controls.
- Delivered CLI utilities (`scripts/ingest.py`, `scripts/eval_run.py`, enhanced `scripts/rollback.py`) with consistent argparse help.
- Expanded ingestion metadata (breadcrumbs, model version, token spans) and added admin session log viewer plus metrics rollups under `logs/metrics/`.
- Added CED-specific chunking pipeline (`scripts/chunk_ced.py`) and smoke evaluation set (`eval/ced-362-smoke.csv`).
- Provisioned GitHub Actions workflows for linting/testing, evaluation gating, and tagged releases.
- Added CODEX operator prompt (`CODEX_PROMPT.md`), API schema generator (`scripts/generate_api_docs.py` + `docs/api/openapi.json`), and `dev.http` request collection with Windows installation guidance for Ghostscript/Tesseract.

### Changed
- Updated retrieval fallback responses to include bullet citations and clearer "I don't know" handling.
- Refreshed documentation (README, docs/README.md) to reflect new commands, CI gates, chunking workflow, and API documentation automation.
- Hardened ingestion CLI summary serialization and applied Ruff auto-fixes/mypy typing refinements across ingestion and CED tooling.

### Evaluation
- nDCG@10: **0.55** (Δ +0.55)
- Recall@50: **0.60** (Δ +0.60)
- MRR: **0.5333** (Δ +0.5333)
- Artifacts: `eval/runs/20250921/`

## [0.1.0] - 2025-09-20
### Added
- Seeded content taxonomy (`content/model`, `content/software`, `content/service`) with AC7070 collateral.
- Implemented ingestion pipeline with deterministic embeddings, JSON logging, and index snapshotting.
- Added retrieval helpers, observability metrics recorder, and ingestion CLI (`scripts/run_ingestion.py`).
- Delivered pytest evaluation harness with gold set, baseline metrics, and daily run exports.

### Evaluation
- nDCG@10: **1.00** (Δ +0.00)
- Recall@50: **1.00** (Δ +0.00)
- MRR: **1.00** (Δ +0.00)
- Artifacts: `evaluation/runs/20250920/235132/`

### Models
- Embeddings: `text-embedding-3-large`
- LLM: `gpt-4.1`
