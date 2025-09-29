# Audit Summary

Update — Phases 6 & 7 were implemented. Tooling, CI, and documentation have materially improved and align with the plan.
Remaining blockers sit primarily in Phases 1–3, while DX/CI and docs are stable and only need incremental follow-up.

Summary of current state:

- Phases 6–7: Largely compliant (details below). Minor follow‑ups remain (version parity checks, optional vulnerability posture notes).
- Phases 1–3: Medium/High gaps persist (pgvector config, RBAC integration tests, glossary runbook) and still require remediation before declaring these phases done.

## Phase 6 — Developer Experience & CI (Audit)

Pass

- Prettier + Tailwind sorting configured and enforced via `.prettierrc.json` and pre‑commit; ESLint Tailwind plugin enabled (`.eslintrc.json`).
- Makefile `quality` target chains Python + Next gates and audits: `lint`, `typecheck`, `test`, `web-lint`, `web-typecheck`, `web-build`, `web-audit`.
- GitHub Actions adds a dedicated frontend job running `npm run lint`, `typecheck`, `build` on Node 20 with a Postgres/pgvector service; uploads audit artifacts (knip, icon audit, route inventory, Python vulture) under `reports/ci/`.
- Pre‑commit runs Ruff, mypy, ESLint, Prettier, markdownlint; Windows‑friendly set‑up documented.
- Node and Python toolchains pinned (Node 20, Python 3.12); caches used.

Gaps / Suggestions

- Formatter choice: Plan mentioned Black, but the repo uses Ruff formatter (Black‑compatible). This is fine; update any lingering “Black” references to avoid confusion.
- Optional: Consider a lightweight CI assertion that `VERSION` == `package.json.version` to catch drift automatically.

## Phase 7 — Documentation & Release (Audit)

Pass

- Documentation updated across README/ARCHITECTURE/OPERATIONS/TROUBLESHOOTING/REQUIREMENTS to the Next.js + pgvector + Prisma + Auth.js stack with Windows instructions and CI parity notes.
- CHANGELOG includes 0.7.0 with clear highlights (DX, CI, audits, docs). `VERSION` file introduced and synced with `package.json` (0.7.0).
- Release process captured in `RELEASE.md` (quality gates, tagging, upgrade/rollback playbook). README links back to AGENTS and release docs as required.
- Editor and project hygiene: `.editorconfig`, `.vscode/extensions.json`, `LICENSE` (SPDX), and language‑appropriate `.gitignore` present.

Gaps / Suggestions

- Ensure `README.md` and `RELEASE.md` instruct checking that `VERSION` and `package.json` remain in lockstep (already implied—consider a tiny CI check to assert equality).
- Optional: Add a docs checklist to PR template confirming README/CHANGELOG were updated when code changes require documentation edits.

## Phase 0

- ✅ Environment scaffolding now mirrors `AppSettings` (Auth.js, SMTP, rate limiting, logging) with placeholder defaults in `.env.example` and `scripts/generate_env.py`.
- ✅ `AppSettings` accepts both `CONTENT_ROOT` and `CONTENT_DIR`, removing the earlier mismatch.
- ✅ TROUBLESHOOTING captures dependency failure logging guidance for `pip-sync`/`npm install` scenarios.

## Phase 1

- Medium – No migration ensures `set_config('app.pgvector_lists', …)` exists before verifying IVFFlat; the verification script still assumes the config has been set upstream. Consider a bootstrap migration or doc update clarifying how to seed the GUC.

## Phase 2

- ✅ Next.js `/api/ask` now streams upstream SSE chunks, normalises error payloads, and the chat/admin UI no longer exhibits mojibake.

## Phase 3

- ✅ FastAPI admin endpoints now require the configured `X-Admin-Token`, and tests assert unauthenticated access is rejected.
- ✅ Glossary APIs emit contract-compliant error payloads with `request_id` propagation.
- ✅ `docs/glossary-spec.md` reflects the new Prisma schema and reviewer workflow.
- Medium – Add integration coverage proving non-admin users cannot access `/api/glossary` or `/admin` (e.g., Playwright + API tests).
- Low – Document glossary provisioning/rollback steps in OPERATIONS/TROUBLESHOOTING to satisfy the runbook requirement.

## Open Questions

1. Where should `app.pgvector_lists` be initialised so migrations and verification scripts agree (database init script vs. Prisma migration)?
1. Should we codify a CI assertion that `VERSION`, `package.json`, and FastAPI metadata stay in lockstep?
1. What form should cross-stack RBAC integration tests take (Playwright end-to-end vs. API tests with mocked auth)?

## Suggested Next Steps

1. Introduce a bootstrap migration (or documented DBA step) that sets `app.pgvector_lists` so `make db.verify` never fails on new environments.
2. Add integration tests covering RBAC restrictions for `/api/glossary` and `/admin`, then extend OPERATIONS/TROUBLESHOOTING with glossary provisioning + rollback guidance.
3. Add an automated check (e.g., unit test or CI step) asserting `VERSION`, `package.json.version`, and FastAPI metadata stay aligned.

## Phase 4

- ✅ Legacy FastAPI UI assets live only under `archive/legacy-ui/`, AGENTS reflects Framer Motion as optional, and docs render cleanly.

## Phase 5

- ✅ `web/` subfolders were removed and `REPO_STRUCTURE.md` documents the current layout.

## Audit Overview (Phases 0–5)

— Phase 0 — Safety & Baseline —

- Status: Complete.
- Evidence: `.env.example`, `scripts/generate_env.py`, `atticus/config.py`, `TROUBLESHOOTING.md` cover required keys, placeholders, and failure logging.
- Notes: New contributors can satisfy AGENTS baseline without leaking secrets.

— Phase 1 — Data Layer First —

- Status: Partial (pending pgvector GUC bootstrap).
- Evidence: `prisma/migrations/20240708123000_pgvector_schema/migration.sql`, `scripts/verify_pgvector.sql`, `lib/prisma.ts`.
- Gaps/Risks: `make db.verify` assumes `app.pgvector_lists` exists; cold environments may fail verification.
- Remediation: Add a migration or documented DBA step to seed `app.pgvector_lists` before verification.

— Phase 2 — RAG Contract Unification —

- Status: Complete.
- Evidence: `app/api/ask/route.ts`, `components/chat/chat-panel.tsx`, `app/admin/page.tsx`, `app/api/glossary/utils.ts`.
- Notes: SSE streaming, encoding fixes, and error normalisation delivered.

— Phase 3 — Auth & RBAC Hardening —

- Status: Partial (tests/runbook outstanding).
- Evidence: `api/routes/admin.py`, `tests/test_admin_route.py`, `docs/glossary-spec.md`, `app/api/glossary/utils.ts`.
- Gaps/Risks: Need cross-stack RBAC tests and glossary lifecycle documentation.
- Remediation: Add RBAC integration coverage and extend OPERATIONS/TROUBLESHOOTING with glossary runbook content.

— Phase 4 — Frontend Hygiene —

- Status: Complete.
- Evidence: `archive/legacy-ui/`, `AGENTS.md`, `ARCHITECTURE.md`.
- Notes: Next.js guidance aligned; legacy folders archived.

— Phase 5 — Orphans & Structure Cleanup —

- Status: Complete.
- Evidence: `REPO_STRUCTURE.md`, repository tree.
- Notes: No lingering FastAPI UI directories.

## Combined Implementation & Debug Plan (Phases 0–5)

Goal: remedy gaps to attain a 95% working app with stable data model, streaming `/api/ask`, enforced RBAC, and clean UI.

Phase 0 — Env & Safety

- Add all required keys to `.env.example` matching `AppSettings` (Auth.js, SMTP, rate limit, logging, sandbox flags).
- Replace sensitive generator defaults with placeholders; rename `CONTENT_DIR` → `CONTENT_ROOT`.
- Debug: `python scripts/generate_env.py --force --ignore-env`; `python scripts/debug_env.py`; verify expected keys resolved.
- Acceptance: `npm run audit:py`, `npm run audit:routes`, `npm run audit:ts` run without env-related failures.

Phase 1 — Prisma & pgvector

- Fix `prisma/schema.prisma` duplicates and `GlossaryEntry.synonyms` type.
- Update `app_private.update_updated_at()` (or add per-table triggers) for `updated_at` columns.
- Re-run: `npx prisma migrate dev --name fix-schema`, `npm run prisma:generate`, `make db.migrate`.
- Verify: `make db.verify` with `PGVECTOR_DIMENSION`/`PGVECTOR_LISTS`.
- Acceptance: `prisma validate` OK; `db.verify` success.

Phase 2 — Ask Contract & Streaming

- Implement true streaming in `app/api/ask/route.ts` forwarding upstream SSE/body chunks; set `Content-Type: text/event-stream`, `Cache-Control: no-transform`, `Connection: keep-alive`.
- Fix mojibake in chat/admin; ensure ASCII or correct entities.
- Normalize errors to global contract with `request_id` and optional `fields`.
- Tests: Expand `tests/unit/ask-client.test.ts` (chunk boundaries, fallback JSON) + Playwright happy-path.
- Acceptance: Incremental events received; UI renders sources; tests green.

Phase 3 — RBAC & Glossary

- Enforce server-side RBAC on FastAPI admin (`/admin/dictionary`…) using a role-check dependency; return 401/403 appropriately.
- Standardize Next glossary error responses to include `request_id`.
- Docs: Update `docs/glossary-spec.md` to match Prisma schema/workflows.
- Tests: Pytest and Playwright to ensure non-admin is blocked; admin CRUD works.
- Acceptance: Protected endpoints reject unauthorized users; admin flows pass; docs aligned.

Phase 4 — Frontend Hygiene

- Remove `web/static` and `web/templates` (archive if needed), ensure no references remain.
- Decide on Framer Motion: add minimal variants or drop from AGENTS + package.json.
- Run `npm run audit:ts` and resolve unused imports/components; confirm Tailwind purge coverage via `npm run build` size checks.
- Acceptance: Lint/typecheck clean; audits clean; build succeeds; docs reflect final stack.

Phase 5 — Orphans & Structure

- Update `REPO_STRUCTURE.md` and `ARCHITECTURE.md` to match final tree and canonical Next.js UI.
- Rename `web-dev` target to `app-dev` (or document alias) to avoid confusion.
- Run `python scripts/audit_unused.py --json` to confirm no orphaned Python routes/utilities.
- Acceptance: No orphans flagged; repo/docs/Makefile aligned.

## Debug Workflow & Gating

- After each phase run: `npm run lint`, `npm run typecheck`, `npm run test:unit`, `pytest -q`, `npm run build`, `npm run audit:ts`, `make db.verify`.
- Observe runtime: `logs/app.jsonl`, `logs/errors.jsonl`; confirm SSE via `curl -N http://localhost:3000/api/ask`.
- CI parity: ensure the above runs in CI (added in Phase 6 later) but validate locally now.

## End-to-End Smoke for 95% Target

- `make db.up && make db.migrate && make db.seed`.
- Start services: `make api` (FastAPI) and `npm run dev` (Next.js).
- Validate flows:
  - Chat: ask, stream answer, sources visible, `X-Request-ID` present.
  - Admin: magic link sign-in, RBAC gate `/admin`, glossary approve path.
  - Contact: submit escalation; verify sandbox mail/log.
- Coverage: ≥90% backend; ≥80% UI; audits pass.

## Risks to Track

- Migration/trigger order (ensure trigger exists before IVFFlat operations).
- SSE behind proxies/load balancers (disable buffering; set `no-transform`).
- Secret management in runners (placeholders for dev; central store for real envs).
- Residual references to `web/` in docs/tools causing confusion.
