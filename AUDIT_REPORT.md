# Audit Report — Atticus (2025-10-04)

## Status Summary

- ✅ FND-001 — Documentation now reflects the Next.js UI workflow (Phase 4).
- ✅ FND-002 — Legacy static UI archived; Next.js app is the only entry point (Phase 4).
- ✅ FND-003 — `/api/ask` contract unified via Next.js proxy + shared DTOs.
- ✅ FND-004 — Versioning sources (`VERSION`, `package.json`, FastAPI) aligned at 0.7.2 with shared release notes.
- ✅ FND-005 — Environment template includes Auth.js, SMTP, and rate-limiting variables required by the Next.js stack.
- ✅ FND-006 — Prisma schema owns pgvector tables/index definitions; Python service consumes the shared schema.
- ✅ FND-007 — Frontend propagates `request_id` via streaming ask client and logs.
- ✅ FND-008 — Audit automation (knip/vulture/route checks/pgvector verification) runs in CI and local make targets.

## Dependency & Usage Overview

- **Next.js (app router)** — entry points under `app/` with shared layout/providers. Auth relies on `next-auth` with Prisma adapter (`lib/auth.ts`, `prisma/schema.prisma`). Glossary admin fetches REST routes at `/api/glossary`.
- **Python RAG services** — FastAPI app (`api/main.py`) mounts ingestion (`ingest`), retrieval (`retriever`), evaluation (`eval`). Vector persistence implemented via psycopg+pgvector (`atticus/vector_db.py`), embeddings from OpenAI (`atticus/embeddings.py`).
- **Data layer** — Prisma migrations cover auth/glossary data plus pgvector tables; Python services consume the shared schema defined in `prisma/schema.prisma`.
- **Tooling** — Make targets drive Python flows; Next.js scripts managed via npm. CI workflows run Ruff, mypy, pytest, pgvector verification, and a frontend job covering lint/typecheck/build plus audits.

## Findings

| ID      | Finding                                                                                                          | Why it’s a problem                                                                                 | Impacted Files/Folders                                                                                                                                              | Fix Steps                                                                                                                                     | Dependencies/Order                                            | Parallelizable? | Est. Effort |
| ------- | ---------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- | --------------- | ----------- |
| FND-001 | README still documents FastAPI UI (`make ui`/`web/static`) instead of Next.js app router                         | Contributors follow wrong setup, missing Auth.js/email requirements and SSE contract               | `README.md` (§Quick Start, Make Targets)【F:README.md†L20-L122】                                                                                                    | ✅ Phase 4 rewrote README to emphasise `make web-dev`, documented Next.js routes, and referenced the legacy archive.                          | After `AUDIT_REPORT.md` approval; prerequisite for onboarding | No              | 1.5d        |
| FND-002 | Legacy static UI (`web/static`) coexists with Next app, README instructs loading both                            | Causes duplicate chat implementations, stale Tailwind animations, confuses `/ask` consumers        | `web/static/*`, `tailwind.config.js` animation entries【F:tailwind.config.js†L8-L15】【F:README.md†L120-L158】                                                      | ✅ Phase 4 archived `web/static`, pruned unused Tailwind animations, and updated docs to point at the Next.js app.                            | Dependent on Phase 5 structure cleanup                        | No              | 1d          |
| FND-003 | `/api/ask` contract unified via Next.js proxy + shared DTOs                                         | Frontend now consumes the FastAPI service consistently with SSE streaming                        | `app/api/ask/route.ts`【F:app/api/ask/route.ts†L1-L120】, `components/chat/chat-panel.tsx`【F:components/chat/chat-panel.tsx†L160-L206】
         | Maintain proxy tests and streaming coverage                                                         | Complete                                                     | No              | 2d          |
| FND-005 | `.env.example` and `scripts/generate_env.py` now include Auth.js, SMTP, rate limiting, and logging settings               | New contributors can boot Auth without manual edits                                          | `.env.example`【F:.env.example†L1-L56】, `scripts/generate_env.py` defaults【F:scripts/generate_env.py†L24-L86】
| FND-006 | Prisma schema and migrations own pgvector tables/indexes; Python reuses the shared schema                            | Eliminates schema drift between Prisma and Python services                                        | `prisma/schema.prisma`【F:prisma/schema.prisma†L1-L84】, `prisma/migrations/20240708123000_pgvector_schema/migration.sql`【F:prisma/migrations/20240708123000_pgvector_schema/migration.sql†L1-L78】
         | Document pgvector configuration (lists/probes) for DBA hand-off (remaining work: seed `app.pgvector_lists` GUC)   | Partial (pending GUC bootstrap)                              | No              | 0.3d        |
| FND-008 | Audit automation (Knip, icon audit, route inventory, pgvector verification) runs via Makefile and GitHub Actions   | Enforces unused-code policy and DB readiness per audit requirements                                | `.github/workflows/lint-test.yml`【F:.github/workflows/lint-test.yml†L1-L87】, `package.json` scripts【F:package.json†L7-L31】
         | Monitor audit outputs and keep TROUBLESHOOTING/OPERATIONS waivers up to date                                      | Complete                                                     | Yes             | 0.3d        |
### Additional Notes & Evidence

- `npm install` reports 8 vulnerabilities; schedule remediation alongside dependency bumping (tracked for Phase 6).【3f34ab†L1-L11】
- Consider adding an automated parity check to assert `VERSION` matches `package.json`/FastAPI metadata (see audit summary).
- RBAC integration tests for `/admin` and `/api/glossary` remain a gap (tracked in Phase 3 notes).
- Continue pruning unused assets flagged by Knip reports in `reports/ci/`.
