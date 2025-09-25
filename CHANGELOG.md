# CHANGELOG — Atticus

All notable changes to this project are documented here following **Semantic Versioning**.
The newest entries appear first.

---

## [Unreleased]

- _No changes yet._

---

## [0.6.1] — 2025-09-29

### Changed
- Escalation email subjects now append the `request_id` (`Escalation from Atticus: AE<INT> · {request_id}`) and mirror the limit
  of three citations in the payload.
- Retrieval logging propagates the `request_id` into `answer_generated` events for trace alignment.

### Fixed
- Chat and `/ask` routes now pass the current `request_id` through the retrieval stack ensuring all downstream logs share the
  same correlation identifier.

---

## [0.6.0] — 2025-09-28

### Added
- Clarification workflow on `/ask` that requests more context for ambiguous queries and surfaces it via API/UI.
- Bullet-aligned answer schema with optional key points, limited citations, and escalation emails capturing structured highlights.
- Confidence-binned evaluation reporting with HitRate@5, CSV confidence columns, and tests covering metrics helpers.
- Release automation target (`make release`) plus streamlined GitHub workflow matching AGENTS guidance.

### Changed
- UI chat bubbles now render summaries, bullet lists, and source metadata for richer responses.
- Escalation logs/emails include bullet sections while CLI supports passing bullet arguments.
- README, OPERATIONS, and API docs updated for new response contract, clarification policy, and evaluation reporting.

### Fixed
- Ensured retrieval confidence estimation is shared across evaluation and runtime for consistent bucket assignment.

---

## [0.5.0] — 2025-09-27

### Added
- OpenTelemetry integration with request spans, trace-aware logging, and configurable OTLP exports.
- `adr/0001-record-architecture-decisions.md` plus `infra/` scaffolding for deployment and collector guidance.
- `scripts/ui_ping.py` and Make targets (`ui-ping`, `next-ae`, `log-escalation`, `e2e`) to exercise ingest → eval → smoke → UI flows.
- Escalation unit tests covering AE counters, schema logging, and email body content.

### Changed
- Escalation logs now emit the mandated JSON/CSV schema with AE IDs starting at `AE100` (no zero padding) and persistent CC/to columns.
- Logging configuration emits human-readable console logs by default with optional JSON/trace enrichment; subjects now follow `Escalation from Atticus: AE<INT>`.
- README/OPERATIONS updated with telemetry env vars, new directory layout, and governance via Commitizen pre-commit hook.

### Fixed
- Atomic escalation counter writes prevent duplicate AE IDs across concurrent escalations.
- Request middleware attaches trace/span attributes to logs, ensuring consistent correlation across metrics and email payloads.

---

## [0.4.0] — 2025-09-26

### Added
- Automated escalation routing with AE identifiers, JSON/CSV loggers, and SES notifications aligned with confidence policy.
- PromptService for hot-reloading named prompts plus supporting CLI utilities (`scripts/next_ae_id.py`, `scripts/log_escalation.py`, `scripts/send_email.py`).
- UI escalation banner surfaced on partial answers with configurable timeout.
- Smoke test suite covering 200/206 flows and new Gitleaks pre-commit hook.

### Changed
- `/ask` endpoint now issues 206 responses on low confidence with request/AE IDs, escalated flag, and sources list.
- README, API docs, and Makefile updated with new smoke/send-email targets and escalation guidance.
- Sanitised `.env` defaults removing placeholder secrets and expanding routing metadata.

### Fixed
- Ensured environment diagnostics expose sanitized configuration and PromptService cache invalidates on file changes.

---

## [0.3.0] — 2025-09-25

### Added
- Shared JSON error schema with request/response correlation tests covering 400/401/422/500.
- Diátaxis documentation structure with dedicated escalation policy, reranker deployment, and enhancement outlines.
- `CODEOWNERS`, `API_NAMING_CONVENTIONS.md`, and glossary (`docs/reference/dictionary.yml`) for governance.

### Changed
- Migrated repository to `src/` layout; updated Makefile, scripts, and tooling to respect new paths.
- Expanded `.env.example` to mirror agent-specified defaults and routing metadata.
- Refreshed README, tutorials, and system overview with new commands, diagrams, and references.

### Fixed
- Ensured API error responses include structured payloads and consistent logging, preventing ad-hoc exception leaks.

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

