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
