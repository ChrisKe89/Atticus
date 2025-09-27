# CHANGELOG — Atticus

All notable changes to this project are documented here following **Semantic Versioning**.
The newest entries appear first.

---

## [Unreleased]

### Added
- E2E smoke target now verifies API and UI make commands via `scripts/e2e_smoke.py`.
- New SMTP mailer module `atticus.notify.mailer` and `/contact` route for escalation emails using `.env` SMTP settings.
- Ask schema now accepts `{ "query": "..." }` as an alias for `question`.
- Documentation expanded with `ARCHITECTURE.md`, `OPERATIONS.md`, and `RELEASE.md`.
- Dev HTTP examples updated with `/contact` route.

### Changed
- CI enforces >=90% coverage in `make test`; coverage exemptions documented in `pyproject.toml`.
- Configuration cache hardened to reflect `.env` updates during reload tests.

### Fixed
- Corrected settings regeneration when `.env` or environment variables change.

---

## [0.2.4] — 2025-09-25

### Added
- `scripts/debug_env.py` to print sanitized diagnostics for secrets sourcing.
- Tests covering environment priority selection and conflict reporting for OpenAI API keys.

### Changed
- `.env` secrets preferred by default; can be overridden with `ATTICUS_ENV_PRIORITY=os`.
- Enhanced `scripts/generate_env.py` with `--ignore-env` and fingerprint logging.

---

## [0.2.3] — 2025-09-24

### Changed
- Rebuilt web chat surface with modern layout and collapsible navigation.
- Expanded README with Docker Compose and Nginx reverse-proxy deployment steps.

### Fixed
- Automatic settings regeneration to eliminate stale OpenAI API keys during sessions.

---

## [0.2.2] — 2025-09-22

### Changed
- Bumped patch version to 0.2.2.
- Included `eval/harness` and `scripts` in pytest discovery.
- Cleaned unused `type: ignore` comments and applied Ruff auto-fixes.

---

## [0.2.1] — 2025-09-21

### Fixed
- Windows install failures caused by `uvloop` dependency.
- Improved evaluation harness to allow tests without FAISS/OpenAI installed.

### Added
- OCR resilience with better Tesseract error handling.

---

## [0.2.0] — 2025-09-21

### Added
- Introduced `config.yaml`/`.env` harmony with `atticus.config.load_settings()`.
- CLI utilities for ingestion, evaluation, and rollback.
- Rich ingestion metadata (breadcrumbs, model version, token spans).
- GitHub Actions for linting, testing, evaluation gating, and tagged releases.

### Changed
- Updated retrieval fallback responses to include bullet citations.
- Refreshed documentation and chunking workflow.

### Evaluation
- Baseline metrics recorded: nDCG@10: **0.55**, Recall@50: **0.60**, MRR: **0.5333**.

---

## [0.1.0] — 2025-09-20

### Added
- Initial content taxonomy and ingestion pipeline with deterministic embeddings and JSON logging.
- Retrieval helpers, observability metrics, and ingestion CLI.
- Seeded evaluation harness with gold set and baseline metrics.

