# Audit Consolidated Plan — Atticus

## A. Executive Summary
- Unified the previous implementation plan, audit summary, and report into a single actionable tracker.
- Closed the highest-risk configuration gap by aligning `.env.example` and the generator script with `AppSettings`, adding Auth.js (`NEXTAUTH_*`) variables, reranker toggles, and safer SMTP placeholders.
- Restored editable package installs by wiring `pyproject.toml` to the shared `VERSION` file, enabling local tooling (pytest, mypy, pre-commit) to resolve the `atticus` package without manual `PYTHONPATH` hacks.
- Cleared the lint blocker surfaced in the audit (`tailwindcss/enforces-shorthand`) so Next.js lint/build completes cleanly.
- Documented the residual psycopg import failure that prevents the Python test suite from running inside this container and outlined remediation steps.

## B. Scope & Assumptions
- Reviewed `IMPLEMENTATION_PLAN.md`, `audit_summary.md`, `AUDIT_REPORT.md`, and inspected related source files (Prisma schema/migrations, env tooling, Next.js components, packaging metadata).
- Validated tooling availability by running `npm ci`, `pip install -r requirements.txt`, `pip install -e .`, `npm run lint`, and `npm run build`.
- Assumed local developers can supply a Postgres connection string (`DATABASE_URL`) when executing Prisma commands; placeholder credentials are used in this audit environment.
- Python tests currently require a functional `psycopg` binary distribution. The container lacks a working import path during pytest collection despite successful ad-hoc imports; remediation is tracked as a blocker below.

## C. Completed vs Pending Matrix
| Item | Source Doc | Status | Evidence |
| --- | --- | --- | --- |
| Align `.env.example` with Auth.js/SMTP expectations | audit_summary.md §Phase 0, AUDIT_REPORT FND-005 | ✅ Done | `.env.example`, `scripts/generate_env.py` updated to include `NEXTAUTH_*`, reranker toggles, and sanitized SMTP defaults. |
| Document env requirements in README | implementation_plan.md Phase 0 | ✅ Done | README environment step references `NEXTAUTH_SECRET`/`NEXTAUTH_URL`. |
| Restore editable installs (`pip install -e .`) | audit_summary.md §Phase 6, AUDIT_REPORT FND-004 | ✅ Done | `pyproject.toml` now reads version from `VERSION`; `pip install -e .` succeeds. |
| Resolve Tailwind padding lint warnings | audit_summary.md §Phase 4 | ✅ Done | `components/site-header.tsx`, `components/ui/textarea.tsx` use `p-*` shorthands; `npm run lint` clean. |
| Verify Prisma schema integrity | implementation_plan.md Phase 1 | ✅ Done | `npx prisma validate` succeeds with placeholder `DATABASE_URL`. |
| Run Python pytest suite | implementation_plan.md Cross-Phase Testing, audit_summary.md Phase 3 | ⏳ Blocked | `pytest` fails with `ModuleNotFoundError: psycopg.rows`; investigation required (see Risks/Blockers). |
| Address `npm audit` findings | AUDIT_REPORT.md Known Issues | ⏳ Pending | 8 vulnerabilities remain (`npm ci` output). |
| Extend release workflow parity (`release.yml`) | audit_summary.md Phase 6 Gaps | ⏳ Pending | Not addressed in this pass. |

## D. Risks / Blockers
1. **Pytest import failure (`psycopg.rows`)** – Despite successful manual imports, pytest collection fails with `ModuleNotFoundError: No module named 'psycopg.rows'; 'psycopg' is not a package`. Hypothesis: coverage or pytest path rewriting is loading a namespace stub before the binary wheels initialise. *Remediation:* pin `psycopg==3.1.18` (known-good), or adjust `atticus/vector_db.py` to defer importing `psycopg.rows` until runtime with a clearer error and skip tests when the dependency is missing. Track a follow-up issue to reproduce locally and document required `libpq` libraries if that proves to be the root cause.
2. **Security posture** – `npm ci` reports 8 vulnerabilities (3 low, 4 moderate, 1 critical). Upstream fixes not yet applied; continue to monitor, document waivers in `OPERATIONS.md`, and schedule dependency bumps.

## E. Phased Plan (P1…Pn)
- **P0 – Safety & Env Hygiene**
  1. Regenerate `.env` via `python scripts/generate_env.py --force --ignore-env`; confirm Auth.js, SMTP, rate limiting, logging, and reranker keys are present.
  2. Update README/RELEASE/TROUBLESHOOTING with any new required variables.
  3. Acceptance: `.env.example` matches `atticus.config.AppSettings`; `scripts/generate_env.py` uses placeholders only.
- **P1 – Data Layer Validation**
  1. Run `DATABASE_URL=<uri> npx prisma validate` and `DATABASE_URL=<uri> npx prisma db pull` (dry-run) to confirm migrations and schema alignment.
  2. Execute `make db.migrate` followed by `make db.verify` against a local Postgres with pgvector enabled.
  3. Acceptance: Prisma migrations apply without errors; verification SQL passes.
- **P2 – Ask Contract & Streaming QA**
  1. Exercise `/api/ask` SSE proxy via `npm run dev` + `curl -H "Accept: text/event-stream" http://localhost:3000/api/ask` with a mock backend; ensure incremental chunks propagate.
  2. Expand frontend tests (Vitest/Playwright) to assert bullet rendering and error normalization.
  3. Acceptance: streaming events include `start/answer/end`; UI renders clean characters without mojibake.
- **P3 – RBAC & Admin Hardening**
  1. Add integration coverage ensuring FastAPI admin routes enforce `X-Admin-Token` and Next.js APIs include `request_id` in error responses.
  2. Update docs/glossary runbooks with provisioning/rollback guidance.
  3. Acceptance: Unauthorized requests receive 401/403 with contract-compliant payloads; docs aligned.
- **P4 – Frontend Hygiene**
  1. Keep lint/style checks green (`npm run lint`, `npm run build`, `npm run audit:ts`).
  2. Periodically review `components/*` for Tailwind shorthand compliance and remove stale dependencies (e.g., Framer Motion if unused).
  3. Acceptance: No ESLint Tailwind warnings; audit scripts clean.
- **P5 – Orphans & Release Parity**
  1. Update GitHub `release.yml` to mirror frontend quality gates (lint/typecheck/build) before tagging.
  2. Address outstanding `npm audit` items or document waivers.
  3. Acceptance: Release workflow passes the same checks as PR CI; vulnerability backlog triaged.

## F. Fix Log
- [#001] Environment template parity
  - **Root Cause:** `.env.example` and `scripts/generate_env.py` omitted Auth.js (`NEXTAUTH_*`), reranker toggles, and used production-like SMTP credentials, conflicting with `AppSettings` and onboarding requirements.
  - **Files/Lines:** `.env.example`, `scripts/generate_env.py`, `README.md` (env step), `CHANGELOG.md` (Unreleased).
  - **Change:** Added `NEXTAUTH_SECRET`, `NEXTAUTH_URL`, reranker defaults, safer SMTP placeholders, and documentation updates.
  - **Test/Verification:** `npm run lint`, `npm run build`, `pip install -e .`.
  - **Status:** ✅ Done.
- [#002] Editable install & version alignment
  - **Root Cause:** `pyproject.toml` lacked a `version`, breaking `pip install -e .` and blocking pytest/mypy workflows flagged in audit Phase 6.
  - **Files/Lines:** `pyproject.toml`, `CHANGELOG.md`.
  - **Change:** Declared `dynamic = ["version"]` and bound to the shared `VERSION` file; documented in changelog.
  - **Test/Verification:** `pip install -e .` (successfully builds editable wheel).
  - **Status:** ✅ Done.
- [#003] Tailwind padding lint warnings
  - **Root Cause:** Components used redundant `px-*`/`py-*` combinations (triggering `tailwindcss/enforces-shorthand`).
  - **Files/Lines:** `components/site-header.tsx`, `components/ui/textarea.tsx`.
  - **Change:** Replaced duplicate padding pairs with `p-*` shorthand classes.
  - **Test/Verification:** `npm run lint`, `npm run build`.
  - **Status:** ✅ Done.

## G. Verification Plan
| Command | Purpose | Result |
| --- | --- | --- |
| `npm ci` | Install Node dependencies | Completed with warnings about upstream package vulnerabilities. |
| `pip install -r requirements.txt` | Sync Python dependencies | Completed; upgraded `beautifulsoup4` and `colorama`. |
| `pip install -e .` | Validate editable install | Succeeds after pyproject fix. |
| `npm run lint` | ESLint (Next.js) | Pass – no warnings after padding fix. |
| `npm run build` | Next.js production build | Pass – see `/tmp/build.log` tail summary. |
| `DATABASE_URL=postgresql://atticus:atticus@localhost:5432/atticus npx prisma validate` | Prisma schema validation | Pass. |
| `pytest -n0` | Python test suite | ❌ Fails: `ModuleNotFoundError: psycopg.rows`; see Risks/Blockers for follow-up. |

## H. Artifacts & Diffs
- Branch: `chore/audit-fix/20250928-1758-b7779b8` (this audit pass).
- Pending PR: `Full audit → fixes → consolidated plan`.
- Key updated files: `.env.example`, `scripts/generate_env.py`, `pyproject.toml`, `components/site-header.tsx`, `components/ui/textarea.tsx`, `CHANGELOG.md`, `README.md`, `docs/audit_consolidated.md`.

