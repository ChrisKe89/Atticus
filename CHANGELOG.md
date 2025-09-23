# Changelog

## [Unreleased]

### Added

- SMTP mailer module `atticus.notify.mailer` and `/contact` route that sends escalation emails using `.env` SMTP settings.
- Ask schema now accepts `{ "query": "..." }` as an alias for `question`.
- Docs: added `ARCHITECTURE.md`, `OPERATIONS.md`, `RELEASE.md`.
- Dev HTTP: added `/contact` example.

### Changed

- Enforce ≥90% coverage in CI and `make test`; documented temporary coverage exemptions under `[tool.coverage.run].omit`.

## [0.2.3] - 2025-09-24

### Fixed

- Regenerate application settings automatically when `.env` or runtime environment variables change, eliminating stale OpenAI API
  key fingerprints during web sessions.

### Changed

- Rebuilt the web chat surface with a modern layout, collapsible navigation, and refreshed styling to match the new HTML
  specification.
- Expanded `README.md` with Docker Compose deployment steps plus nginx reverse-proxy instructions for TLS fronting.

## [0.2.2] - 2025-09-22

### Changed

- Bump patch version to 0.2.2.
- Align pytest discovery to include `eval/harness` and `scripts` in `pyproject.toml` and VS Code workspace.
- Remove unused `type: ignore` comments flagged by mypy in parsers and FAISS modules.
- Applied Ruff auto-fixes to reduce lint noise in scripts.

## [0.2.1] - 2025-09-21

### Fixed

- Windows install failure by replacing `uvicorn[standard]` with `uvicorn` and excluding `uvloop` on Windows; regenerated `requirements.txt` to keep `httptools`, `websockets`, and `watchfiles`.
- Evaluation harness: lazy-load heavy imports and fix `main()` settings initialization to allow unit tests without FAISS/OpenAI available.
- OCR resilience: guard Tesseract OCR calls in PDF/image parsers; ingestion no longer fails if Tesseract binary is missing.

### Operations

- Ran full ingestion over `content/` and generated FAISS index and manifest.
- Executed smoke evaluation; artifacts written under `eval/runs/YYYYMMDD/`.

## [0.2.0] - 2025-09-21

### Added

- Introduced `config.yaml`/`.env` harmony via `atticus.config.load_settings()` and new chunking environment controls.
- Delivered CLI utilities (`scripts/ingest_cli.py`, `scripts/eval_run.py`, enhanced `scripts/rollback.py`) with consistent argparse help.
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
