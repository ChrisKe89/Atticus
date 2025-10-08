# CHANGELOG — Atticus

All notable changes to this project are documented here following **Semantic Versioning**.
The newest entries appear first.

---

## [Unreleased]

### Changed

- Consolidated the active backlog into `TODO_NEW.md`, updated cross-references, and recorded completed tasks in `ToDo-Complete.md`.
- Resolved merge artefacts in `VERSION` to restore 0.7.2 as the canonical release number and flagged the follow-up automation in the backlog.

---

## [0.7.4] — 2025-10-07

### Changed


- Streamlined the chat workspace to focus on live conversations and removed legacy highlight cards.
- Hid the Settings navigation link for unauthenticated visitors and removed redundant contact escalation callouts.
- Cleared footer navigation links to maintain spacing without duplicate destinations.

### Testing

- `npm run lint`
- `npm run typecheck`
- `npm run build`

- Switched the CED chunker to a zero-overlap default across configuration, ingestion scripts, and metadata snapshots.
- Allowed explicit `CHUNK_OVERLAP_TOKENS=0` in environment configuration and documentation so bespoke corpora can opt back into overlap deliberately.

### Documentation

- Highlighted the zero-overlap behaviour in the README quick start and CED chunking guide.

### Testing

- `PYTHONPATH=. pytest tests/test_ingestion_retrieval_integration.py -vv`


---

## [0.7.3] — 2025-10-06

### Changed

- Documented the required environment export before running `make db.verify` and removed the redundant Prisma client generation step from the README developer workflow.
- Added source attribution, hashed fingerprints, and sanitized snapshots to `python scripts/debug_env.py` by implementing `atticus.config.environment_diagnostics`.

### Added

- Regression coverage for the new environment diagnostics helper to ensure secrets remain redacted while reporting their provenance.

### Testing

- `ruff check .`
- `ruff format --check .`
- `mypy atticus api ingest retriever eval`
- `PYTHONPATH=. pytest tests/test_hashing.py tests/test_config_reload.py tests/test_mailer.py tests/test_chunker.py tests/test_seed_manifest.py tests/test_eval_runner.py tests/test_environment_diagnostics.py`
- `PYTHONPATH=. pytest tests/test_chat_route.py tests/test_contact_route.py tests/test_error_schema.py tests/test_ui_route.py tests/test_admin_route.py`
- `PYTHONPATH=. pytest tests/test_ingestion_retrieval_integration.py -vv`
- `npm run test:unit`
- `npm run lint`
- `npm run typecheck`
- `npm run build`
- `npm run audit:ts`
- `npm run audit:icons`
- `npm run audit:routes`
- `npm run audit:py`

---

## [0.7.2] — 2025-10-05

### Changed

- Synchronized all version sources (`VERSION`, `package.json`, FastAPI metadata) at 0.7.2 and documented the change in the audit report.
- Trimmed resolved findings from `audit_summary.md` and `AUDIT_REPORT.md`, highlighting the remaining remediation work for Phases 0–5.
- Updated `TODO.md`/`ToDo-Complete.md` to remove completed items, backfill commit references, and keep the active backlog authoritative.
- Clarified that Framer Motion is optional in `AGENTS.md`, aligning guidance with current dependencies.

### Fixed

- Marked finished audit tasks as complete, ensuring the ledger, audit summary, and changelog stay in sync.

---

## [0.7.1] — 2025-10-05

### Added

- Web and database security assessment recorded at `reports/security/2025-10-05-web-db-assessment.md`, detailing dependency vulnerabilities, configuration hardening, and pgvector prerequisites.

### Changed

- Bumped repository version to 0.7.1 to publish the audit findings and align `package.json`/`VERSION` metadata.

### Security

- Flagged critical Next.js 14.2.5 advisories (cache poisoning, image optimisation DoS/injection) and outlined mitigation steps, including immediate upgrade guidance for `next`, `next-auth`, and supporting tooling.

## [0.7.0] — 2025-09-28

### Added

- Prettier configuration (with Tailwind sorting), ESLint tailwindcss plugin, and local hooks to enforce formatting for shadcn/ui components.
- `VERSION` file as the single source of truth for release numbers and alignment with `package.json`.
- GitHub Actions `frontend-quality` job (Node 20 + Postgres service) uploading audit artifacts from Knip, route inventory, and Python dead-code scan.
- `scripts/icon-audit.mjs` for lucide-react import hygiene without relying on Knip plugins.

### Changed

- `make quality` now chains Ruff, mypy, pytest, Next.js lint/typecheck/build, and audit scripts to mirror CI.
- `.pre-commit-config.yaml` runs ESLint and Prettier alongside Ruff/mypy/markdownlint for consistent developer experience.
- `.eslintrc.json` extended with tailwindcss plugin + Prettier compatibility; package scripts updated with `format` / `format:check`.
- README, AGENTS, IMPLEMENTATION_PLAN, ARCHITECTURE, OPERATIONS, TROUBLESHOOTING, REQUIREMENTS, and RELEASE docs rewritten for the Next.js + pgvector stack, CI gates, and release workflow.
- `.github/workflows/lint-test.yml` expanded with audit artifact uploads; `.gitignore` ignores `reports/ci/` outputs.

### Known Issues

- `npm audit` reports one critical (Next.js middleware) and seven moderate/low vulnerabilities without upstream fixes as of 2025-09-28. Mitigations documented in OPERATIONS/TROUBLESHOOTING pending vendor patches.

### Testing

- `make quality`
- `npm run lint`
- `npm run typecheck`
- `npm run build`
- `pytest --maxfail=1 --disable-warnings --cov=atticus --cov=api --cov=retriever --cov-report=term-missing --cov-fail-under=90 -q`

---

## [0.5.3] — 2025-10-04

### Added

- Next.js `/api/ask` route proxying the FastAPI retriever with SSE support and shared TypeScript/Pydantic DTOs.
- Streaming chat client (`components/chat/chat-panel.tsx`) with typed `lib/ask-client.ts` helper and Vitest coverage for SSE parsing.
- Prisma migration extending `GlossaryEntry` with synonyms and review metadata alongside tests for the FastAPI admin dictionary route.

### Changed

- FastAPI `AskResponse` now returns `sources` objects (`path`, `page`, `heading`, `chunkId`, `score`) and honours `contextHints`/`topK` overrides.
- Glossary admin UI exposes synonyms, review notes, and reviewer timestamps; TROUBLESHOOTING now documents Auth.js magic link and SSE debugging steps (including PowerShell flows).
- `.env.example` documents the `RAG_SERVICE_URL` required for the Next.js proxy, and README details the streaming `/api/ask` contract.

### Testing

- `npm run test:unit`
- `pytest tests/test_chat_route.py`
- `pytest tests/test_admin_route.py`

## [0.5.2] — 2025-09-30

### Added

- Prisma models and migrations for `atticus_documents` and `atticus_chunks`, aligning pgvector storage with the shared data layer.
- `make db.verify` target plus CI workflow to run `scripts/verify_pgvector.sql` against a pgvector-enabled Postgres service.

### Changed

- Documented pgvector verification steps in README, OPERATIONS, and TROUBLESHOOTING with PowerShell equivalents.
- Noted `psycopg[binary]` usage in Python tooling to keep local workflows consistent with Prisma migrations.

### Testing

- `npm run db:migrate` _(fails locally without Postgres; covered in CI)_
- `make db.verify` _(requires `psql` client; enforced in CI)_
- `npm run audit:ts`

---

## [0.6.2] — 2025-09-29

### Added

- In-memory pgvector repository test double covering ingestion reuse and retrieval ranking behaviour.
- Integration coverage ensuring the ingestion pipeline writes manifests/metadata and retrieval answers honour citations.

### Changed

- Regenerated Python dependency lockfile (`requirements.txt`) via `pip-compile` to capture upstream security updates.

### Testing

- `pytest tests/test_chunker.py tests/test_seed_manifest.py`
- `pytest tests/test_ingestion_retrieval_integration.py`

---

## [0.6.1] — 2025-09-28

### Added

- Regression test for the seed manifest generator plus contributor checklist guidance.
- HTML evaluation dashboard (`metrics.html`) emitted alongside CSV/JSON artifacts and exposed via API/CLI.

### Changed

- `make test.unit` now executes seed manifest and evaluation artifact tests to keep ingestion guardrails enforced.
- README and reports documentation updated to describe deterministic evaluation artifacts and CI uploads.

### Testing

- `pytest tests/test_seed_manifest.py`
- `pytest tests/test_eval_runner.py`
- `pytest tests/test_mailer.py`
- `pytest tests/test_chunker.py`

---

## [0.6.0] — 2025-10-01

### Added

- CED chunkers with SHA-256 dedupe, ingestion manifest updates, and a `make seed` workflow for deterministic seed manifests.
- SMTP escalation allow-list enforcement, trace payload attachments, and admin metrics dashboards with latency histograms.
- Sample evaluation artifact scaffolding under `reports/` and glossary specification documentation.

### Changed

- Logging now propagates trace IDs across events and metrics capture P95 latency plus histogram buckets.
- API middleware enforces per-user/IP rate limiting with structured 429 responses and hashed identifiers.
- README, OPERATIONS, REQUIREMENTS, and TROUBLESHOOTING guides updated for ingestion, observability, and guardrail workflows.

### Testing

- `pytest tests/test_mailer.py`
- `pytest tests/test_chat_route.py`

---

## [0.4.1] — 2025-09-28

### Added

- Dedicated `make smoke`, `make test.unit`, and `make test.api` targets for lightweight verification workflows.

### Changed

- Unified the `/ask` endpoint to return the canonical `{answer, citations, confidence, should_escalate, request_id}` contract and removed the duplicate chat handler.
- Disabled FastAPI's autogenerated docs and removed the placeholder root route now that the UI is fully served by Next.js.
- Bumped the API/Next.js workspace version to 0.4.1.

### Fixed

- Legacy static chat client now renders citations and escalation notices from the canonical API response shape.

---

## [0.5.1] — 2025-09-27

### Fixed

- Resolved Auth.js and RBAC type regressions by aligning session shape, callback signatures, and server helpers with NextAuth definitions.
- Restored TypeScript coverage for glossary admin handlers and unit tests, unblocking `npm run typecheck`.

### Testing

- `npm run typecheck`
- `npm run test:unit`

---

## [0.5.0] — 2025-09-27

### Added

- Auth.js email magic link authentication with Prisma adapter, Postgres schema, and RLS enforcement.
- Database-backed glossary admin APIs plus UI gated to `ADMIN` role; persisted glossary storage with author/audit metadata.
- Vitest unit tests and Playwright RBAC journey along with Make targets (`db.*`, `web-test`, `web-e2e`) and runbook documentation.

### Changed

- Site navigation now reflects session state (sign-in/out) and protects `/admin` behind middleware + server checks.
- Docker Compose, Makefile, and README updated for Postgres lifecycle, Prisma migrations, and auth onboarding.

---

## [0.4.0] — 2025-09-27

### Added

- Next.js workspace with routes for chat, admin, settings, contact, and apps plus Tailwind styling.
- Shared layout with responsive navigation, hero components, and contextual admin tiles.

### Changed

- Makefile commands now proxy Next.js workflows (`make ui`, `make web-build`, `make web-start`).
- Project version bumped to 0.4.0 across the API and frontend manifest.

### Removed

- Legacy Jinja2/Eleventy templates and static Tailwind build scripts.

---

## [0.3.0] — 2025-09-27

### Changed

- Standardized API error responses on the shared JSON schema with request ID propagation and regression tests for 400/401/422/5xx cases.

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
