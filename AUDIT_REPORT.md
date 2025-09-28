# Audit Report — Atticus (2025-10-04)

## Status Summary
- ✅ FND-001 — Documentation now reflects the Next.js UI workflow (Phase 4).
- ✅ FND-002 — Legacy static UI archived; Next.js app is the only entry point (Phase 4).
- ✅ FND-003 — `/api/ask` contract unified via Next.js proxy + shared DTOs.
- ⚠️ FND-004 — Versioning drifts between frontend (`0.5.1`) and backend (`0.6.2`).
- ⚠️ FND-005 — Environment template omits Auth.js, SMTP, and Prisma variables required by the Next.js stack.
- ⚠️ FND-006 — Prisma schema lacks pgvector tables/index definitions; Python service owns vector schema separately.
- ✅ FND-007 — Frontend propagates `request_id` via streaming ask client and logs.
- ⚠️ FND-008 — Audit automation (knip/vulture/route checks/pgvector verification) absent prior to this pass.

## Dependency & Usage Overview
- **Next.js (app router)** — entry points under `app/` with shared layout/providers. Auth relies on `next-auth` with Prisma adapter (`lib/auth.ts`, `prisma/schema.prisma`). Glossary admin fetches REST routes at `/api/glossary`.
- **Python RAG services** — FastAPI app (`api/main.py`) mounts ingestion (`ingest`), retrieval (`retriever`), evaluation (`eval`). Vector persistence implemented via psycopg+pgvector (`atticus/vector_db.py`), embeddings from OpenAI (`atticus/embeddings.py`).
- **Data layer** — Prisma migrations cover auth/glossary tables only (`prisma/migrations/20240702120000_auth_rbac`). Vector tables are managed ad-hoc by Python scripts, not Prisma.
- **Tooling** — Make targets drive Python flows; Next.js scripts managed via npm. CI workflows run Ruff, mypy, pytest, and eval gate; no frontend lint/typecheck/build executed in CI.

## Findings

| ID | Finding | Why it’s a problem | Impacted Files/Folders | Fix Steps | Dependencies/Order | Parallelizable? | Est. Effort |
| -- | ------- | ------------------ | ---------------------- | --------- | ------------------ | --------------- | ----------- |
| FND-001 | README still documents FastAPI UI (`make ui`/`web/static`) instead of Next.js app router | Contributors follow wrong setup, missing Auth.js/email requirements and SSE contract | `README.md` (§Quick Start, Make Targets)【F:README.md†L20-L122】 | ✅ Phase 4 rewrote README to emphasise `make web-dev`, documented Next.js routes, and referenced the legacy archive. | After `AUDIT_REPORT.md` approval; prerequisite for onboarding | No | 1.5d |
| FND-002 | Legacy static UI (`web/static`) coexists with Next app, README instructs loading both | Causes duplicate chat implementations, stale Tailwind animations, confuses `/ask` consumers | `web/static/*`, `tailwind.config.js` animation entries【F:tailwind.config.js†L8-L15】【F:README.md†L120-L158】 | ✅ Phase 4 archived `web/static`, pruned unused Tailwind animations, and updated docs to point at the Next.js app. | Dependent on Phase 5 structure cleanup | No | 1d |
| FND-003 | `/api/ask` lives only in FastAPI (`api/routes/chat.py`), Next app has no matching route or client integration | Frontend cannot call RAG service consistently; contract diverges from AGENTS spec | `api/routes/chat.py`【F:api/routes/chat.py†L27-L92】, `app/page.tsx` (static demo)【F:app/page.tsx†L1-L120】, `AGENTS.md` contract section【F:AGENTS.md†L200-L236】 | Implement Next.js route handler proxying FastAPI or move logic to Next, create shared TypeScript DTO, update client components and tests | Depends on Phase 2 plan (contract unification) | No | 2d |
| FND-004 | Version drift: frontend `package.json`=0.5.1 vs backend FastAPI app version=0.6.2, changelog only tracks backend | Breaks semantic version policy and release automation | `package.json`【F:package.json†L3-L38】, `api/main.py` version constant【F:api/main.py†L39-L47】, `CHANGELOG.md` headers【F:CHANGELOG.md†L9-L24】 | Define single source of version truth (e.g., `VERSION` file), bump both runtimes together, update changelog+docs | Should happen before next release | No | 0.5d |
| FND-005 | `.env.example` lacks Auth.js SMTP/magic link variables (EMAIL_SERVER_*, AUTH_SECRET, NEXTAUTH_URL) | New contributors cannot boot Auth, causing runtime errors | `.env.example`【F:.env.example†L1-L17】, `lib/auth.ts` requirements【F:lib/auth.ts†L58-L122】 | Expand template with NextAuth + SMTP settings, document Windows-friendly generation commands | Can ship with Phase 0 safety updates | Yes | 0.5d |
| FND-006 | Prisma schema has no pgvector tables/indexes; vector DDL managed separately in Python | Risk of schema drift, migrations unaware of vector tables, pgvector extension enablement unchecked | `prisma/schema.prisma`【F:prisma/schema.prisma†L1-L76】, `atticus/vector_db.py` manual schema creation【F:atticus/vector_db.py†L96-L165】 | Model vector tables/extensions in Prisma (or documented SQL migrations), ensure migrations enable pgvector and enforce embedding dimension | Depends on Phase 1 data layer work | No | 2d |
| FND-007 | Next frontend lacks request_id/telemetry propagation; no logging hooks despite contract | Hinders tracing/escalation correlation between UI and backend | `app/page.tsx` static UI (no API calls/logging)【F:app/page.tsx†L1-L120】, `AGENTS.md` logging requirements【F:AGENTS.md†L238-L282】 | Implement fetch helpers capturing `request_id`, integrate structured logging (e.g., analytics or console) and surface errors | After `/api/ask` contract unified | No | 1d |
| FND-008 | Automation gaps: no knip, icon audit, route graph, or pgvector verification scripts | Hard to enforce unused-code policy and DB readiness; contradicts audit requirements | Absent scripts (now added) and npm scripts list【F:package.json†L7-L33】 | Add audit scripts (`npm run audit:*`, `scripts/audit_unused.py`, `scripts/verify_pgvector.sql`, `scripts/route-audit.mjs`) and document usage | Immediate (this change) | Yes | 0.5d |

### Additional Notes & Evidence
- `npm install` reports 8 vulnerabilities; schedule remediation alongside dependency bumping (tracked for Phase 6).【3f34ab†L1-L11】
- CI workflows currently omit Next.js lint/typecheck/build; add matrix stage during Phase 6 (`.github/workflows/lint-test.yml`).【F:.github/workflows/lint-test.yml†L1-L43】
- No Framer Motion usage detected via `rg 'framer-motion'` (0 hits); plan to remove dependency or implement animations in Phase 4.
- Initial knip scan flags `prisma/seed.ts`, `scripts/route-audit.mjs`, and legacy `web/static/js/script.js` as unused; Phase 4 archived the static assets under `archive/legacy-ui/` ahead of further pruning.

