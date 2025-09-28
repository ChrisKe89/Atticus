# Audit Summary

- High risk gaps remain across Phases 0–3: env scaffolding is incomplete, Prisma migrations fail on updated-at triggers, SSE work is simulated rather than streamed, and FastAPI admin endpoints still bypass RBAC.
- Several deliverables (docs, UI polish) lag behind the implemented schema/UX requirements and include obvious defects (e.g., mojibake characters, outdated glossary spec).
- Immediate remediation is required before treating Phases 0–3 as complete or moving on to later phases.

## Phase 0

- High – .env.example omits required secrets (Auth.js, email, rate limiting, logging flag, Azure toggle) so new contributors cannot satisfy the AGENTS baseline (.env.example:4-19; compare against expected inputs in atticus/config.py:72-143).
- High – scripts/generate_env.py writes live-looking SMTP credentials into .env by default (scripts/generate_env.py:42-53), creating a leakage risk; defaults must be placeholders.
- Medium – The generator emits CONTENT_DIR, but the settings loader only honors CONTENT_ROOT, leaving the app to fall back to defaults unexpectedly (scripts/generate_env.py:41 vs atticus/config.py:75-84).
- Medium – Neither .env.example nor the generator includes RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW_SECONDS, LOG_FORMAT, EMAIL_SANDBOX, etc., so make quality/API rate limiting will diverge from documented guardrails (scripts/generate_env.py:25-63, .env.example:4-19).
- Medium – No evidence the TROUBLESHOOTING update records dependency failures from npm install/pip-sync as mandated by the phase acceptance criteria (the section is present but lacks actual findings).

## Phase 1

- Critical – prisma/schema.prisma defines AtticusDocument/AtticusChunk twice (prisma/schema.prisma:116-190), so prisma validate and generated clients will fail; phase deliverable not shippable.
- High – The shared trigger app_private.update_updated_at() still targets camelCase (NEW."updatedAt") while the new vector tables use snake_case (updated_at), causing CREATE TRIGGER to abort at migration time (prisma/migrations/20240702120000_auth_rbac/migration.sql:10-16 vs prisma/migrations/20240708123000_pgvector_schema/migration.sql:74-82).
- High – GlossaryEntry.synonyms is declared as String[] @db.Text, which Prisma does not permit for array columns; codegen will error (prisma/schema.prisma:95-107).
- Medium – No migration ensures set_config('app.pgvector_lists', …) exists before verifying IVFFlat; the verification script assumes the trigger ran cleanly (scripts/verify_pgvector.sql:1-72) but the migration fails earlier.
- Low – Missing documentation tying scripts/verify_pgvector.sql into CI acceptance criteria; Makefile adds db.verify, but there is no workflow update yet.

## Phase 2

- High – The Next.js /api/ask handler pulls the entire upstream JSON response before emitting three SSE events, so clients never receive incremental tokens (no real streaming) and long responses buffer in memory (app/api/ask/route.ts:39-103). Acceptance criteria around “streamed responses via SSE” are unmet.
- Medium – Chat UI renders mojibake separators (�) instead of ASCII bullets for citations, indicating encoding/regression in the new panel (components/chat/chat-panel.tsx:179-181).
- Medium – Similar mojibake appears in the admin metadata title (“Admin � Atticus”), signaling inconsistent charset handling across the UI refresh (app/admin/page.tsx:48).
- Low – Error responses from the new ask proxy surface raw upstream payloads without harmonising to the documented error schema (no request_id, missing fields), undermining contract guarantees.

## Phase 3

- Critical – FastAPI admin endpoints remain completely unauthenticated/unauthorised: the router exposes /admin/dictionary et al. with no RBAC checks (api/routes/admin.py:18-116), and the regression test suite still exercises them without credentials (tests/test_admin_route.py:16-43). This violates “RBAC enforced server-side” acceptance criteria.
- High – The new Next.js glossary APIs return bare {error: ...} bodies without request identifiers or consistent error codes, diverging from the global error contract (app/api/glossary/utils.ts:72-85).
- Medium – docs/glossary-spec.md still documents the legacy schema and API (e.g., status: String, DictionaryPayload), contradicting the Prisma model and new routes (docs/glossary-spec.md:18-46).
- Medium – Playwright/Next RBAC coverage exists only at the helper level (lib/rbac.ts:1-39; tests/unit/rbac.test.ts:4-43); there’s no integration test proving non-admins are blocked from /api/glossary or /admin.
- Low – TROUBLESHOOTING covers Auth.js updates, but there’s no audit trail documenting glossary provisioning/rollback steps demanded by the phase goals.

## Open Questions

1. Should the ask proxy stream upstream SSE events instead of buffering JSON? If upstream cannot stream yet, do we document an exemption?
1. What is the intended secret management policy for SMTP credentials now that generate_env embeds values?
1. How will RBAC be enforced on the FastAPI side—middleware injection, dependency-based gating, or eventual deprecation of those endpoints?

## Suggested Next Steps

1. Patch the Prisma schema/migrations to remove duplicate models, fix trigger functions for snake_case tables, and ensure synonyms uses a supported column type. Re-run prisma migrate dev to confirm success.
1. Align .env.example and scripts/generate_env.py with the required config set (placeholders only), and add missing keys so python scripts/generate_env.py produces a working .env without leaking secrets.
1. Replace the ask proxy with a true streaming bridge (or document/implement a temporary polling fallback) and fix mojibake in the UI components.
1. Add RBAC enforcement to FastAPI admin routes (and corresponding tests), update glossary docs to the new schema, and ensure error payloads include request_id per contract.
1. After remediation, rerun the documented audit scripts/tests (npm run audit:ts, make quality, pytest ...) to verify 90%+ coverage and contract conformance.

## Phase 4

- Medium - Legacy `web/static` directory still exists (albeit empty) alongside the archived assets, so the repo cleanup called out in IMPLEMENTATION_PLAN.md remains unfinished (`web/static`).
- Medium - AGENTS stack guidance still mandates Framer Motion even though the dependency has been removed, which will mislead future contributors about required UI tooling (AGENTS.md:75-80).
- Low - `ARCHITECTURE.md` retains control characters (`\u001a`) in its component table, leaving the Phase 4 documentation polish incomplete and risking downstream parsing/rendering issues (ARCHITECTURE.md:17).

## Phase 5

- Medium - Empty `web/` subfolders (`web/static`, `web/templates`) are still present, contradicting the "orphan cleanup" objective and signalling that FastAPI UI remnants were not fully retired.
- Low - `REPO_STRUCTURE.md` omits the lingering `web/` tree, so the published structure map diverges from the actual repository layout (REPO_STRUCTURE.md:5-27).

## Audit Overview (Phases 0–5)

— Phase 0 — Safety & Baseline —

- Intended: Branch creation; complete env scaffolding; audit tool scripts runnable.
- Evidence: `.env.example:4-19`, `scripts/generate_env.py:25-63`, `atticus/config.py:75-143`, `package.json: scripts`.
- Status: Partial.
- Gaps/Risks: Missing keys vs `AppSettings`; sensitive defaults in generator; alias mismatch (`CONTENT_DIR` vs `CONTENT_ROOT`).
- Remediation: Align `.env.example` + generator with `AppSettings`; remove sensitive defaults; add `RATE_LIMIT_REQUESTS`, `RATE_LIMIT_WINDOW_SECONDS`, `LOG_FORMAT`, `EMAIL_SANDBOX`.

— Phase 1 — Data Layer First —

- Intended: Prisma models for pgvector; migrations; verification wired.
- Evidence: Duplicate models `prisma/schema.prisma:116-190`; trigger function camelCase vs snake_case `updated_at`; `GlossaryEntry.synonyms` annotated incorrectly; verification present `scripts/verify_pgvector.sql`, `Makefile:37`.
- Status: Fail (migration integrity).
- Gaps/Risks: `prisma generate/validate` break; migration order/trigger failure.
- Remediation: Remove duplicate models; correct `synonyms`; fix/update triggers; re-run migrations and verify IVFFlat.

— Phase 2 — RAG Contract Unification —

- Intended: Unified `/api/ask` contract; real SSE; UI shows sources/errors.
- Evidence: Proxy buffers full JSON then emits events `app/api/ask/route.ts:39-103`; mojibake in chat/admin; contracts/tests exist.
- Status: Partial.
- Gaps/Risks: No incremental streaming; encoding defects; error schema gaps.
- Remediation: Implement true streaming; fix encoding; normalize errors to include `request_id` and `fields`.

— Phase 3 — Auth & RBAC Hardening —

- Intended: Enforce RBAC in server actions; glossary review metadata; docs/runbooks updated.
- Evidence: Prisma RBAC + glossary review migration; FastAPI admin routes lack RBAC; glossary error utils return bare errors; runbook updated.
- Status: Partial.
- Gaps/Risks: Server-side RBAC missing for FastAPI admin; inconsistent error schema.
- Remediation: Add RBAC dependency to FastAPI admin routes; standardize error payloads; update tests/docs.

— Phase 4 — Frontend Hygiene —

- Intended: Tailwind paths; Framer Motion decision; shadcn/ui normalization; unused assets removed.
- Evidence: Tailwind content paths OK; Framer Motion not used but mandated in AGENTS; `web/static` remains (empty); shadcn/ui used in components.
- Status: Partial.
- Gaps/Risks: Tooling-doc mismatch (Framer); lingering empty folders.
- Remediation: Remove `web/static`/`web/templates` or archive; update AGENTS to optionalize or reintroduce FM minimally.

— Phase 5 — Orphans & Structure Cleanup —

- Intended: Remove FastAPI UI vestiges; update repo structure/docs; clarify make targets.
- Evidence: `web/` folders persist; `REPO_STRUCTURE.md` omits them; Makefile target named `web-dev` (not `ui`).
- Status: Partial.
- Gaps/Risks: Structural drift; confusing targets.
- Remediation: Remove lingering `web/` folders; align docs; rename/document targets.

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
