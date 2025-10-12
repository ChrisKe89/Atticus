# All Documentation

## Index
- [AGENTS.md](#agents-md)
- [app/README.md](#app-readme-md)
- [ARCHITECTURE.md](#architecture-md)
- [archive/legacy-ui/README.md](#archive-legacy-ui-readme-md)
- [CHANGELOG.md](#changelog-md)
- [code.md](#code-md)
- [codex_instructions.md](#codex-instructions-md)
- [CONTRIBUTING.md](#contributing-md)
- [docs/api/README.md](#docs-api-readme-md)
- [docs/ATTICUS_DETAILED_GUIDE.md](#docs-atticus-detailed-guide-md)
- [docs/glossary-spec.md](#docs-glossary-spec-md)
- [docs/README.md](#docs-readme-md)
- [docs/REMOTE_ACCESS.md](#docs-remote-access-md)
- [docs/runbooks/auth-rbac.md](#docs-runbooks-auth-rbac-md)
- [IMPLEMENTATION_PLAN.md](#implementation-plan-md)
- [OPERATIONS.md](#operations-md)
- [README.md](#readme-md)
- [RELEASE.md](#release-md)
- [REPO_STRUCTURE.md](#repo-structure-md)
- [REPO_TREE.md](#repo-tree-md)
- [REQUIREMENTS.md](#requirements-md)
- [scripts/rollback.md](#scripts-rollback-md)
- [SECURITY.md](#security-md)
- [seeds/README.md](#seeds-readme-md)
- [STYLEGUIDE.md](#styleguide-md)
- [TODO.md](#todo-md)
- [TODO_COMPLETE.md](#todo-complete-md)
- [TROUBLESHOOTING.md](#troubleshooting-md)

## AGENTS.md

<!-- Begin file: AGENTS.md -->

# AGENTS — Atticus

> Single source of truth for agent behavior, pipelines, and guardrails. Target stack: **Next.js + Postgres/pgvector + Prisma + Auth.js (Email magic link first, Azure AD later)**.

---

## Current Audit Status

- Refer to [AUDIT_REPORT.md](AUDIT_REPORT.md) for the latest findings (FND-001 – FND-008).
- Follow [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for phased remediation tied to [TODO.md](TODO.md).
- Run `make quality` (Ruff + mypy + pytest + Next lint/typecheck/build + audits) before opening a PR.
- Release 0.7.4 streamlines the chat workspace and contact surface; keep the Settings nav gated behind authentication.

## Execution Criteria — **Must‑Follow for Repo Work**

> Treat these as hard requirements for anyone (or any agent) touching the repo.

### Instructions

- Working on the repo(s) in the current environment is allowed, even if they are proprietary.
- Analyzing code for vulnerabilities is allowed.
- Showing user code and tool call details is allowed.
- User instructions may overwrite the _CODING GUIDELINES_ section in this document.
- Do not use `ls -R`, `find`, or `grep` — these are slow in large repos. Use `rg` and `rg --files`.
- If completing the task requires writing or modifying files:
  - **Coding Guidelines**
    - Fix problems at the root cause rather than surface-level patches.
    - Avoid unneeded complexity; ignore unrelated bugs or broken tests.
    - Update documentation as necessary.
    - Keep changes minimal, focused, and consistent with existing style.
    - Frontend/TypeScript code uses **Prettier** (with Tailwind sorting) + **ESLint** (Next + tailwindcss plugin). Run `npm run format` for writes and `npm run lint` for checks.
    - Python uses the **Ruff formatter** (`ruff format`) and **Ruff** linting; no Black.
    - **Never** add copyright/license headers unless requested.

### Persistence

- Keep going until the user’s query is completely resolved **before** ending your turn.
- Only stop when you are sure the problem is solved.
- Don’t ask for mid‑way confirmation — make the most reasonable decision, proceed, and document assumptions.

### Tool Preambles

- Begin by rephrasing the user’s goal concisely **before** calling any tools.
- Immediately outline a structured plan of steps you’ll follow.
- While editing, narrate progress succinctly and sequentially.
- Finish by summarizing completed work separately from the plan.

### Self‑Reflection (internal)

- Develop an internal rubric for quality (5–7 categories) before acting.
- Iterate using the rubric until the solution meets a high bar across categories.

### Code Editing Rules

**Context understanding** — be thorough; use tools to get the full picture; bias toward not asking the user. If an edit only partially fulfills the request, gather more info or use more tools before finishing.

**Guiding principles** — Clarity & Reuse; Consistency; Simplicity; Demo‑orientation; Visual quality.

**Frontend stack defaults** — Framework: Next.js (TypeScript); Styling: TailwindCSS; UI: shadcn/ui; Icons: Lucide; State: project‑specific.

**UI/UX best practices** — Visual hierarchy: 4–5 sizes, `text-xs` for captions, avoid `text-xl` unless hero; Color: one neutral + up to two accents; Spacing: multiples of 4; Fixed‑height containers with internal scrolling; State: skeletons/`animate-pulse`; Accessibility: semantic HTML/ARIA; prefer Radix/shadcn.

**Exploration** — decompose request; map scope; check deps; resolve ambiguity; define output contract; plan execution.

**Verification** — verify as you go; exit long‑running processes; prefer faster paths.

**Efficiency** — plan, execute, verify efficiently. Use Markdown only where semantically correct (inline code, fenced code, lists, tables). Use `\(` and `\)` for inline math and `\[ \]` for block math.

---

## App Framework (authoritative)

### UI

- **Frameworks:** Next.js (TypeScript)
- **Styling:** Tailwind CSS
- **UI Components:** shadcn/ui
- **Icons:** Lucide
- **Animation:** Framer Motion (optional; add only when a feature needs motion)
- **Fonts:**
  - **Headings & Body:** Inter (single-family stack for simplicity and performance)
    - Load via `next/font/google` and self‑hosted subset; fallbacks: `ui-sans-serif, system-ui`.

### App (server & routing)

- Next.js Route Handlers for API (streamed responses via **SSE**).
- Pages: `/` (chat), `/admin`, `/settings`, `/contact`, `/apps`.
- Shared header/nav pattern; role‑gated admin.
- FastAPI hosts JSON APIs only; any historical UI assets remain under `archive/legacy-ui/` for reference.

### DB

- **Postgres with pgvector**
  - IVFFlat + cosine; `vector_cosine_ops` avoids manual normalization.
  - Cosine measures angle between vectors — good default for text embeddings.
  - Use `probes` 4–8 initially; tune for recall/latency.

- **Metadata for filtering** — `doc_id`, `source`, `product`, `version`, `acl`, `org_id`, `updated_at`, `sha256`.
  - Enables facets (e.g., only product X, version ≥ 2.1).
  - `sha256` of raw text supports de‑dup/change detection.
  - `org_id` + `acl` ⇒ multi‑tenant + group visibility.

- Store `embedding_model` and `embedding_version` with each row.

### ORM

- **Prisma** for schema & migrations.

### Auth

- **Auth.js (NextAuth)** — email magic link first.
- **Azure AD** — to be implemented later (OIDC provider).

### Testing (layers quick map)

- **Smoke** — app boots; auth works; chat stream; admin opens.
- **Unit** — pure functions: chunking, serializers, rerankers, prompts (fixtures).
- **API/Integration** — route handlers with real Postgres (test DB), Prisma, pgvector queries.
- **Retrieval eval** — Recall@k / MRR@k / exact match vs gold set.
- **E2E** — Playwright: sign‑in → ask → streamed answer → admin log/escalation.
- **Policy/DB** — RLS and role gates enforced in SQL, not just UI.
- **Perf/sanity** — latency + token‑count guards; basic rate‑limit check.

---

## Document Map

- **README.md** — Project overview, quick start, and run commands
- **ARCHITECTURE.md** — System diagram and request/response flows
- **REQUIREMENTS.md** — Functional & non‑functional requirements
- **OPERATIONS.md** — Deploy, backups, monitoring, incident playbook
- **TROUBLESHOOTING.md** — Common issues & fixes
- **CHANGELOG.md** — Versioned changes
- **CODE.md** — Consolidated source (for quick reference)

---

## Purpose

Atticus is a Retrieval‑Augmented Generation (RAG) assistant designed to answer staff questions using curated documents and escalate low‑confidence queries for human follow‑up. It ingests your content, retrieves the most relevant passages, and produces grounded answers with citations. If confidence falls below the threshold, Atticus provides a cautious partial answer and escalates via email.

---

## System Overview (target state)

### UI & API

- **Next.js (TypeScript)** app for chat + admin
- **Tailwind** + **shadcn/ui** + **Lucide** + optional **Framer Motion**
- Streaming answers via **SSE** route handlers
- **Auth.js (NextAuth)** — start with **Email (magic link)**; add **Azure AD (OIDC)** later for SSO

### Data

- **Postgres + pgvector** for relational data and embeddings (Docker for dev; Supabase acceptable for hosted)
- **Prisma ORM** for schema & migrations

### RAG

- Ingest → Chunk → Embed → Store
- Retrieve (vector + filters) → Compose context → Generate → Cite → Log
- Confidence threshold → **Escalation** (email), or answer with caveats

#### Model Disambiguation Contract

- When the question clearly names a specific model (e.g., “Apeos C4570”), scope retrieval to that model’s family and emit a single answer with family-scoped citations.
- When the model cannot be inferred confidently, the API must return a `clarification` payload listing the available families (“Apeos C7070 range”, “Apeos C8180 series”). The UI renders the clarification card and resubmits the original question with the selected `models` array.
- When multiple models are detected or supplied, fan out retrieval per model, return `answers[]` with `{ model, family, sources[] }`, and keep the aggregated `sources` in the response for compatibility with downstream tooling.
- Capture low confidence turns only after a full answer is generated—skip collection on clarification-only responses.

### Security

- Role‑based UI and API; **Row‑Level Security (RLS)** in Postgres for org isolation
- Secrets in env only; PII redaction in logs

---

## Configuration & Feature Flags

**Core**

- `DATABASE_URL`, `NEXTAUTH_SECRET`, `EMAIL_SERVER`, `EMAIL_FROM`
- SMTP: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`

**RAG**

- `GEN_MODEL`, `EMBED_MODEL`, `EMBEDDING_VERSION`, `TOP_K`, `CONFIDENCE_THRESHOLD`

**Flags**

- `ENABLE_AZURE_AD=false`
- `EMAIL_SANDBOX=true`
- `RATE_LIMIT_PER_MINUTE=5`
- `LOG_FORMAT=json`

**Windows‑friendly examples (`.env.local`)**

```dotenv
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/atticus?schema=public"
NEXTAUTH_SECRET="dev-secret"
EMAIL_SERVER="smtp://localhost:1025"
EMAIL_FROM="atticus@localhost"
SMTP_HOST="localhost"
SMTP_PORT=1025
SMTP_USER=""
SMTP_PASS=""
SMTP_FROM="atticus@localhost"
GEN_MODEL="gpt-4o-mini"
EMBED_MODEL="text-embedding-3-large"
EMBEDDING_VERSION="2025-01-01"
TOP_K=8
CONFIDENCE_THRESHOLD=0.70
ENABLE_AZURE_AD=false
EMAIL_SANDBOX=true
RATE_LIMIT_PER_MINUTE=5
LOG_FORMAT=json
```

Diagnostics:

```bash
python scripts/debug_env.py
```

---

## API Contracts (authoritative)

### `POST /api/ask`

**Request**

```json
{
  "question": "string",
  "contextHints": ["optional", "strings"],
  "topK": 8
}
```

**Response**

```json
{
  "answer": "string",
  "sources": [{ "path": "content/example.pdf", "page": 3 }],
  "confidence": 0.82,
  "request_id": "abc123",
  "should_escalate": false
}
```

### `POST /api/contact`

**Request**

```json
{
  "reason": "user_clicked_contact|low_confidence|feedback",
  "transcript": ["... prior turns ..."]
}
```

**Response**

```json
{
  "status": "queued",
  "ticket_id": "AE100",
  "request_id": "def456"
}
```

**Status Codes** — `200, 202, 400, 401, 403, 422, 429, 5xx` (errors follow the Error JSON below).

---

## Data Model (outline)

**Accounts & Sessions** — `users(id, email, name, role, created_at)`; `sessions(id, user_id, session_token, expires, created_at)`

**Chat & Traces** — `chats` / `messages` / `rag_events` / `events` (audit timeline: escalated/assigned/resolved)

**Knowledge & Retrieval** — `documents` / `chunks` (with `embedding VECTOR(D)`, `embedding_model`, `embedding_version`, `sha256`) / `glossary`

> **Embedding model isolation:** one model per index (dimension **D** fixed).

---

## Chunking Policy — **CED** (Apeos Customer Expectation Document)

1. **Prose (H2 blocks)** — one chunk per H2 section (paragraphs under the sub‑heading). Metadata: `h1`, `h2`, `page_start/end`, `section_order`, `chunking=\"semantic\"`.
2. **Tables** — Yield/spec: one chunk per logical row (or small row‑group). Wide model×spec tables: chunk as **(spec × model)** pairs. Serialize rows to compact NL (keep units). Metadata: `h1`, `h2`, `table_id`, `row_key`, `model[]|models`, `units`, `page_range`, `source=\"table\"`, `chunking=\"table_row\"|\"spec_model\"`.
3. **Footnotes/notes** — one chunk per note block. Metadata: `note_ref`, `applies_to`.
4. **Series‑wide facts** — `scope=\"series\"`, `model=[C7070,...]`.
5. **Token sizes** — Prose: **400–700** with ~10% overlap. Tables: no overlap.
6. **Page chunks** — only if a page is truly stand‑alone; mark `chunking=\"page\"`.

---

## Indexing & Retrieval

- **Similarity:** cosine (`vector_cosine_ops`) — no manual normalization
- **ANN index:** **IVFFlat**; lists by corpus size (<50k→50–100; 50k–500k→100–400; >500k→400–1000); query‑time `probes` 4–8
- **Filters:** use metadata (`doc_id`, `product`, `version`, `org_id`, `acl`, `chunking`, `h1/h2`, `table_id`)
- **Re‑embed plan:** new vector column/table on model change → backfill batches → switch reads at >80% → prune old

---

## Generation & Escalation

- Concise, sourced answers with citations back to `documents/chunks`.
- If `confidence < threshold` or out‑of‑scope → cautious partial answer + **escalation email**.
- **Ticketing Policy** — create tickets with prefix `AE` and 3‑digit numeric sequence starting at **AE100** (e.g., AE100, AE101...).
  - Escalation payload includes: user, chat/message ids, top‑k docs & scores, exact question, and `request_id`.

**Error JSON (contract)**

```json
200 OK
{"answer":"...","sources":[{"path":"content/example.pdf","page":3}],"confidence":0.82,"request_id":"abc123"}
```

```json
400 Validation
{"error":"validation_error","detail":"'question' is required","fields":{"question":"missing"},"request_id":"abc123"}
```

```json
422 Partial ingestion
{"status":"partial","succeeded":12,"failed":1,"errors":[{"doc":"/content/x.pdf","reason":"pdf parse failed"}],"request_id":"abc123"}
```

```json
5xx Internal
{"error":"internal_error","detail":"see logs","request_id":"abc123"}
```

---

## Logging & Telemetry

- **Format** — structured JSON logs (`LOG_FORMAT=json`) with `level`, `timestamp`, `request_id`, `route`, `user_id` (if present), `latency_ms`.
- **Locations** — app logs to `logs/app.jsonl`; error logs to `logs/errors.jsonl`; DB logs via provider dashboard.
- **Propagation** — generate a `request_id` at the edge and pass through all layers (API → retrieval → mailer); return it in responses and include it in escalations.
- **Metrics** — record counters/gauges/histograms for retrieval latency, tokens in/out, `Recall@k`, `MRR@k`. Emit CSV snapshots to `reports/metrics-<date>.csv`.

---

## Testing Strategy (what to run and in what order)

**Make/NPM targets**

1. `make install` → deps; `make db.up` → Postgres (Docker)
2. `make db.migrate` → Prisma migrations; `make seed` → tiny CED sample
3. `make smoke` → health, auth (test mode), chat stream, admin gate
4. `make test.unit` → chunkers, serializers, helpers
5. `make test.api` → route handlers with real DB
6. `make test.eval` → retrieval metrics vs **gold_set** (Recall@k, MRR@k, exact match)
7. `make test.e2e` → Playwright: sign‑in → ask → stream → see admin log
8. `make quality` → Ruff + mypy + pytest + Next lint/typecheck/build + audits

> CI should run 1→6 on every PR; 7 nightly if slow. Store eval reports under `reports/`.

### Start small — 3 concrete moves

1. **Make targets + npm scripts** — thin wrappers for Windows & CI.
2. **Smoke tests** — assert health/auth/chat/admin/db in <20s.
3. **Retrieval eval** — compute Recall@k (5/8) & MRR@k; produce HTML/CSV under `./reports/` and fail CI on regression.

### What to test specifically (RAG/app)

- **Chunking (CED policy):** H1/H2 + paragraph/table rows → chunks with metadata (`h1`, `h2`, `table_id`, `row_key`, `model[]`, `chunking`), token bounds respected; overlap only on prose.
- **Serializer:** table row → compact sentence includes units and model aliases.
- **Vector search:** cosine, IVFFlat lists/probes set; one test toggles probes (4 vs 8) and asserts stable top‑k for fixed seed.
- **RLS/roles:** `user` cannot read other `org_id`; `reviewer` read but cannot update glossary; `admin` can escalate/resolve — write SQL‑level tests.
- **Streaming:** response arrives in chunks, ends with a well‑formed terminator event; no chunk > N KB.
- **Rate limiting:** 6 rapid requests → 429 on #6 for same user/IP (1‑min window).

### CI shape (GitHub Actions)

- **Matrix:** Node 20 + pgvector service (frontend-quality), Python 3.12 (lint-test), plus release tagging.
- **Jobs:** frontend-quality → lint-test → pgvector-check → eval-gate → release (nightly e2e optional if slow).
- **Artifacts:** `reports/ci/*.json`, `reports/eval-*.{html,csv}`, Playwright traces on failure

### Minimal seed data (keep tests fast)

- 1–2 CED sections (e.g., _Consumables → Toner Cartridge Yield Rate_)
- 6–10 table rows → chunks (one per model or “series”)
- 4–6 prose chunks (H2 blocks)
- Trimmed `gold_set_improved.csv` (10–15 rows) for CI

---

## Operations Cheatsheet

**Local (dev)** — DB up/down: `make db.up` / `make db.down`; migrate/seed: `make db.migrate && make seed`; run app: `make api` + `make web-dev`; quality: `make quality`; tail logs: `npm run logs`.

**Supabase/Hosted (prod)** — daily backups; SQL editor for RLS and IVFFlat; rotate secrets; never commit `.env`.

**Viewing logs** — Next.js route logs (`logs/app-*.log` or `npm run logs`); DB logs (dashboard); escalation traces (ESP dashboard).

---

## UI/UX Best Practices (compact)

- **Hierarchy:** 4–5 font sizes; captions `text-xs`; `text-xl` only for hero/major headings.
- **Color:** one neutral base (e.g., zinc) + up to two accents.
- **Spacing:** multiples of 4; fixed‑height containers with internal scrolling.
- **States:** skeleton placeholders (`animate-pulse`); hover transitions.
- **Accessibility:** semantic HTML/ARIA; prefer Radix/shadcn components.

---

## Security Guardrails

- `.env` is required; no hard‑coded secrets.
- Email via SMTP/SES — restrict `From` and region via env/policy.
- Enforce **RLS** with `org_id` on all tables.
- PII redaction in logs/traces.

---

## Notes on Conflicts (resolved)

- Legacy docs referenced **FastAPI + Jinja2** and **FAISS**. Standardize on **Next.js + Postgres/pgvector + Prisma + Auth.js** as above. Migration tasks are captured in [TODO.md](TODO.md).
- Static HTML prototypes now live under `archive/legacy-ui/`; ship only the Next.js application under `app/`.

---

<!-- End file: AGENTS.md -->

## app/README.md

<!-- Begin file: app/README.md -->

# Wynstan — GC MFD Root-Cause Chat

Baseline Next.js (App Router) workspace for the Wynstan diagnostics experience. Stage 0 establishes tooling so that Stage 1 can layer the UI frame, panes, and skeleton loaders described in `TODO.md`.

## Prerequisites

All development happens with Node.js 20+ and pnpm.

```powershell
node -v   # expect v20.x
pnpm -v   # expect v10+
git --version
```

If any tool is missing, install them before proceeding (see `TODO.md` for Windows-specific commands).

## Getting started

```powershell
pnpm install
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) to confirm the baseline Tailwind styles render. The landing screen includes a badge and status row that should reflect the Tailwind color tokens configured in `src/app/globals.css`.

## Project scripts

| Command       | Purpose                                |
| ------------- | -------------------------------------- |
| `pnpm dev`    | Start Next.js dev server (Turbopack).  |
| `pnpm build`  | Production build.                      |
| `pnpm start`  | Run the compiled build.                |
| `pnpm lint`   | Lint with the Next.js ESLint config.   |

## Tooling stack

- **Next.js 15** (App Router, TypeScript, Turbopack).
- **Tailwind CSS 3.4** configured via `tailwind.config.ts` with shadcn-compatible tokens.
- **shadcn/ui** configuration via `components.json` (manual bootstrap pending CLI registry access).
- **React Query 5** for client data fetching and caching.
- **Zod** for runtime validation.
- **Lucide icons** for consistent iconography.

Utility helpers such as `cn` live in `src/lib/utils.ts`.

## Next steps

Stage 1 tasks will create the shared layout (header/nav), route placeholders, and skeleton states. Track progress and acceptance criteria in `TODO.md`.

<!-- End file: app/README.md -->

## ARCHITECTURE.md

<!-- Begin file: ARCHITECTURE.md -->

# ARCHITECTURE — Atticus

This document provides a **high‑level view of the Atticus system**, showing how data flows through ingestion, retrieval, and answer generation.

---

## System Overview

Atticus is a **Retrieval‑Augmented Generation (RAG)** platform.
It ingests content, builds a searchable vector index, retrieves relevant information on demand, and generates grounded answers.
The Next.js application is the canonical UI; historical static assets live under `archive/legacy-ui/` for reference only.

### Core Components

| Component                  | Responsibility                                                                                                                                                              |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Ingestion & Indexing**   | Parse → chunk → embed → persist vectors + metadata via Prisma migrations and Postgres/pgvector.                                                                             |
| **Retriever & Ranker**     | Vector search with optional lexical rerank; enforces metadata filters (`org_id`, `product`, `version`).                                                                     |
| **Generator**              | Drafts concise, sourced answers using the configured `GEN_MODEL`, respecting confidence thresholds.                                                                         |
| **API Layer**              | FastAPI exposes `/health`, `/ingest`, `/ask`, `/eval`, `/contact` with `/ask` streaming SSE payloads `{answer, sources, confidence, should_escalate, request_id}`.          |
| **Web UI**                 | Next.js App Router served from `/`, delivering chat, admin, settings, contact, and apps routes using shadcn/ui + Tailwind.                                                  |
| **Auth & Sessions**        | Auth.js magic-link flow with Prisma adapter, RLS-backed session storage, and RBAC-aware server actions.                                                                     |
| **Developer Tooling & CI** | Pre-commit (Ruff, mypy, ESLint, Prettier, markdownlint) plus GitHub Actions jobs (`frontend-quality`, `lint-test`, `pgvector-check`, `eval-gate`) mirroring `make quality`. |

---

## Data Flow

1. **Content Addition**
   New or updated documents are added to `content/` and named `YYYYMMDD_topic_version.ext`.

2. **Ingestion**
   Run `make ingest` to parse and chunk documents, compute embeddings, and update the index stored under `indices/`.

3. **Retrieval**
   When a user submits a query, the retriever searches the pgvector index and optionally applies a re-ranker to prioritize the most relevant chunks.

4. **Answer Generation**
   The selected context is passed to the generation model (default `gpt-4.1`) to produce a concise, sourced answer with inline citations.

5. **Escalation (if needed)**
   If the confidence score falls below the configured threshold, the conversation is written to the Prisma `Chat` table with `status='pending_review'`, stored `topSources[]`, and appended `RagEvent` audit rows. Admins can capture follow-up prompts, approve, or escalate these records from the Next.js `/admin` console, which also raises SES escalations when required.

### Ask flow (SSE)

1. Next.js `/api/ask` receives the chat request and validates payloads with shared DTOs in `lib/ask-contract.ts`.
2. The handler proxies the request to the FastAPI `/ask` endpoint.
3. FastAPI returns the canonical JSON payload; when the caller requested SSE, the Next.js proxy emits `start`, `answer`, and `end` events so the UI has a consistent streaming interface.
4. The UI renders the received answer (currently delivered as a single chunk), logs the propagated `request_id`, and stores metadata for escalations.

---

## Supporting Services

- **Observability** — JSON logs (`logs/app.jsonl` and `logs/errors.jsonl`) with request IDs; metrics captured in evaluation runs and exported under `reports/`.
- **Snapshot & Rollback** — Index snapshots stored under `indices/` can be rolled back with `scripts/rollback.py`.
- **Evaluation & Audit Harness** — Retrieval evaluation against the gold set plus frontend audits (`reports/ci/*.json`) surfaced in CI artifacts.

---

## Security Considerations

- All secrets are loaded from `.env` and can be audited with `scripts/debug_env.py`.
- Escalation emails use SES SMTP credentials with IAM policies restricting senders and region (see [SECURITY.md](SECURITY.md)).
- Versioning is centralized in the [`VERSION`](VERSION) file and must align with `package.json` releases.

---

## Cross-References

- [AGENTS.md](AGENTS.md) — Detailed agent responsibilities and error policy.
- [OPERATIONS.md](OPERATIONS.md) — Runbooks and evaluation metrics.
- [README.md](README.md) — Setup instructions and Make targets.

<!-- End file: ARCHITECTURE.md -->

## archive/legacy-ui/README.md

<!-- Begin file: archive/legacy-ui/README.md -->

# Legacy UI Archive

The static HTML prototype previously served from `web/static` has been moved here for
reference. The Next.js application under `app/` is the canonical UI. Do not deploy these
assets; they are retained to preserve historical design notes until parity is confirmed.

<!-- End file: archive/legacy-ui/README.md -->

## CHANGELOG.md

<!-- Begin file: CHANGELOG.md -->

<<<<<<< ours
# CHANGELOG — Atticus

All notable changes to this project are documented here following **Semantic Versioning**.
The newest entries appear first.

---

## [Unreleased]

### Added

- Introduced the model catalog, parser, and resolver to support explicit family scoping, multi-answer payloads, and `/api/ask` clarifications when the model is unknown.
- Added clarification handling in the Next.js UI: the chat panel now renders family selection buttons, resubmits follow-up requests with `models`, and formats multi-model answers with per-answer citations.
- Tagged ingested chunks with `product_family` and `models` metadata, copied the Apeos C8180 series CED into the active corpus, and expanded `eval/gold_set.csv` with cross-family scenarios.
- Added regression coverage for model parsing/resolution, family-scoped retrieval filters, API clarification flows, UI integrations, and a gated Playwright chat clarification scenario.

### Changed

- Consolidated the active backlog into `TODO.md`, updated cross-references, and recorded completed tasks in `TODO_COMPLETE.md`.
- Resolved merge artefacts in `VERSION` to restore 0.7.2 as the canonical release number and flagged the follow-up automation in the backlog.
- Documented the model disambiguation contract across AGENTS, README, and `docs/ATTICUS_DETAILED_GUIDE.md`.

---

## [0.8.1] — 2025-10-20

### Fixed

- Restored Playwright RBAC flows by persisting magic links to the default `./logs/mailbox` directory whenever `AUTH_DEBUG_MAILBOX_DIR` is unset, preserving the ability to disable persistence with an empty value and documenting the fallback for operators.

### Testing

- `npm run test:unit`

---

## [0.8.0] — 2025-10-19

### Added

- Automatic capture of low-confidence chat turns via `captureLowConfidenceChat`, including follow-up prompts, request metadata, and structured audit events stored in the new `RagEvent` ledger.
- Admin follow-up workflow with a review drawer, POST `/api/admin/uncertain/:id/ask-followup`, and deterministic seeds plus UI wiring for tracking prompts alongside escalations.
- Glossary upsert semantics with POST idempotency, PUT updates, inline editing, and audit logging to `rag_events` so term changes remain traceable.
- `scripts/check_version_parity.py` and a `make version-check` gate to keep `VERSION`, `package.json`, and `package-lock.json` synchronized during releases.
- Pgvector configuration migration that enforces the `app.pgvector_lists` GUC and verification SQL ensuring ANN indexes stay aligned with planner expectations.

### Changed

- Admin operations console now surfaces question context, answers, top sources, and follow-up prompts inside a Radix drawer to streamline approvals and escalations.
- Glossary management panel supports inline definition edits, optimistic saves, and PUT-based status transitions backed by rag event auditing.

### Testing

- `PYTHONPATH=. pytest tests/unit/admin-uncertain-route.test.ts tests/unit/glossary-route.test.ts -q`
- `npm run lint`
- `npm run test:unit`
- `CI=1 npm run build`

---

## [0.7.11] — 2025-10-15

### Added

- Prisma `Chat` and `Ticket` models with deterministic seeds plus admin API endpoints for listing, approving, and escalating low-confidence chats.
- Next.js admin operations console with Uncertain, Tickets, and Glossary tabs, including reviewer read-only safeguards and shadcn-powered tabs.
- Vitest coverage for admin API RBAC along with updated Playwright smoke ensuring reviewers stay constrained while admins manage glossary entries end-to-end.

### Testing

- `PYTHONPATH=. pytest tests/unit/admin-uncertain-route.test.ts -q`
- `npm run lint`
- `npm run test:unit`
- `CI=1 npm run build`

---

## [0.7.10] — 2025-10-14

### Added

- Pytest coverage ensuring the FastAPI application metadata reads directly from the repository `VERSION` file so version drift is caught automatically.

### Changed

- FastAPI now loads its version string from the shared `VERSION` file, eliminating manual sync steps with `package.json`.
- Documentation (README, AGENTS, ARCHITECTURE, OPERATIONS, REPO_STRUCTURE, release notes, and workspace settings) explicitly records that Next.js owns the UI while FastAPI serves JSON APIs only.

### Testing

- `pytest tests/test_api_version.py`
- `npm run lint`
- `npm run build`

---

## [0.7.9] — 2025-10-13

### Added

- Introduced shared shadcn-inspired primitives (`Card`, `Badge`) under `components/ui` and extended the button component with `asChild` support via `@radix-ui/react-slot` for consistent navigation styling.

### Changed

- Refreshed the chat workspace, admin overview, glossary management, settings, apps catalogue, and contact escalation form to compose the new card and badge primitives, aligning typography, spacing, and status indicators across the UI.
- Updated the site header to reuse the shared button component for sign-in/out flows and to standardise mobile navigation controls.
- Documented the frontend design system in `README.md` and noted the new dependency in `RELEASE.md` upgrade steps.

### Testing

- `npm run lint`
- `npm run build`

---

## [0.7.8] — 2025-10-12

### Added

- Playwright RBAC coverage to confirm reviewers are redirected from `/admin`, blocked from `/api/glossary`, and that admins can create/delete glossary entries end-to-end.
- Vitest unit tests for Next.js glossary route handlers to assert reviewer read access, admin-only mutations, and reviewer metadata stamping on approvals.

### Changed

- FastAPI admin dictionary tests now assert 403 contracts for invalid tokens, `make quality` runs Vitest + Playwright in addition to existing gates, and documentation reflects the expanded quality bar.

---

## [0.7.7] — 2025-10-11

### Changed

- Documented the glossary review workflow with a Mermaid sequence diagram, decision notes, and backlog links in `docs/glossary-spec.md`.
- Removed the fulfilled Glossary UX backlog item from `TODO.md` and logged completion in `TODO_COMPLETE.md`.

### Testing

- Documentation-only change; no automated tests were run.

---

## [0.7.6] — 2025-10-10

### Added

- Seeded deterministic glossary fixtures (approved, pending, rejected) with dedicated reviewer/author accounts for smoke tests.

### Changed

- Documented glossary seeding, verification, and rollback workflows in `OPERATIONS.md` and `docs/glossary-spec.md`.
- Pruned the completed glossary seed backlog item from `TODO.md` and logged the closure in `TODO_COMPLETE.md`.

### Testing

- `pytest tests/test_seed_manifest.py::test_glossary_seed_entries_round_trip` *(skipped: requires DATABASE_URL and npm in CI/dev)*

---

## [0.7.5] — 2025-10-09

### Added

- Recorded the Phase 0 baseline verification summary in `reports/todo-phase-0-baseline.md` to document current blockers before implementation work begins.

### Changed

- Bumped the tracked release version to 0.7.5 to capture the Phase 0 baseline report.

### Testing

- `make db.verify` (fails: missing `DATABASE_URL` in the execution environment).
- `make quality` (fails: mypy reports an unused `type: ignore` in `ingest/parsers/xlsx.py`).

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
- Updated `TODO.md`/`TODO_COMPLETE.md` to remove completed items, backfill commit references, and keep the active backlog authoritative.
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
=======
# Changelog

## 0.1.1 — 10-Oct-2025

- Added Tailwind CSS 3.4 configuration with shadcn-compatible tokens and utilities.
- Installed baseline UI dependencies: React Query, Zod, Lucide, clsx/tailwind-merge, and tailwindcss-animate.
- Seeded `components.json` to mirror shadcn/ui defaults pending CLI authentication fix.
- Replaced the starter page with a Tailwind-backed placeholder confirming style application.
- Documented setup steps and tooling expectations in `app/README.md`.

## 0.1.0 — 10-Oct-2025

- Scaffolded Next.js 15 App Router project with TypeScript support.
>>>>>>> theirs

<!-- End file: CHANGELOG.md -->

## code.md

<!-- Begin file: code.md -->

# Code Bundle Generator

This file contains a single-script utility (PowerShell) to scan the repository and generate a combined Markdown bundle of all relevant code, Markdown, and JSON files. It excludes logs, build artifacts, caches, binaries, and other non-source outputs.

Quick start:

- From the repo root, run this in PowerShell 7+ (`pwsh`):
  - Copy the script block below into your terminal, or
  - Copy it into a file (e.g., `combine-code.ps1`) and run `pwsh -File combine-code.ps1`.

Output:

- Creates `ALL_CODE.md` at the repo root by default. You can change the output path with `-Output`.

Script:

```powershell
<#
Combine relevant source files into a single Markdown bundle.

Usage examples:
  pwsh -NoProfile -ExecutionPolicy Bypass -File ./combine-code.ps1
  pwsh -NoProfile -ExecutionPolicy Bypass -File ./combine-code.ps1 -Output CODEBASE.md
  pwsh -NoProfile -ExecutionPolicy Bypass -Command "& { <paste this script> }"

Notes:
- Excludes typical build/log/temp directories and non-text file types.
- Includes common source code, Markdown, and JSON files.
- Adds a table-of-contents and per-file fenced code blocks with language hints.
#>

param(
  [string]$Root = (Resolve-Path .).Path,
  [string]$Output = "ALL_CODE.md"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Info([string]$msg) { Write-Host "[info] $msg" }

# Normalize root and output
$Root = (Resolve-Path $Root).Path
$Output = if ([System.IO.Path]::IsPathRooted($Output)) { $Output } else { Join-Path $Root $Output }

# Ensure output is excluded from the scan (if it already exists)
$outputRel = try { [IO.Path]::GetRelativePath($Root, $Output) } catch { '' }

# Extensions to include (code + markdown + json)
$includeExt = @(
  '.ts','.tsx','.js','.jsx','.mjs','.cjs',
  '.py','.sql','.prisma',
  '.css','.scss','.sass','.html','.htm',
  '.sh','.bash','.ps1','.psm1','.psd1',
  '.go','.rs',
  '.md','.markdown','.mdx',
  '.json'
)

# Directories to exclude (typical build/log/temp/binary caches)
$excludeDirs = @(
  '.git','node_modules','.next','dist','build','out','coverage',
  'logs','log','.turbo','.cache','tmp','temp','reports',
  '__pycache__','.pytest_cache','.mypy_cache','.venv','venv',
  '.idea','.gradle','.parcel-cache','.svelte-kit','.husky',
  '.ds_store','.svn','.hg','archive'
)

# Files to exclude (lockfiles, maps, minified, snapshots, binaries, large assets, and our output)
$excludeNamePatterns = @(
  '*.log','*.jsonl','*.map','*.min.*','*.snap','*.lock',
  'pnpm-lock.yaml','package-lock.json','yarn.lock',
  '*.png','*.jpg','*.jpeg','*.gif','*.svg','*.ico','*.pdf',
  '*.zip','*.gz','*.tar','*.tgz','*.7z',
  '*.exe','*.dll','*.bin','*.dylib','*.so','*.class','*.jar','*.pyc',
  '*.ttf','*.otf','*.woff','*.woff2'
)

if ($outputRel -and $outputRel -ne '.') { $excludeNamePatterns += [IO.Path]::GetFileName($Output) }

# Build an exclude regex for directories
$escaped = $excludeDirs | ForEach-Object { [Regex]::Escape($_) } | Where-Object { $_ -and $_.Trim() -ne '' }
$excludeDirRegex = if ($escaped.Count -gt 0) {
  '(?i)(^|[\\/])(' + ($escaped -join '|') + ')([\\/]|$)'
} else {
  $null
}

# Simple ext -> fenced language mapping
$langMap = @{
  '.ts'='ts'; '.tsx'='tsx'; '.js'='js'; '.jsx'='jsx'; '.mjs'='js'; '.cjs'='js';
  '.py'='python'; '.sql'='sql'; '.prisma'='prisma';
  '.css'='css'; '.scss'='scss'; '.sass'='sass';
  '.html'='html'; '.htm'='html';
  '.sh'='bash'; '.bash'='bash'; '.ps1'='powershell'; '.psm1'='powershell'; '.psd1'='powershell';
  '.go'='go'; '.rs'='rust';
  '.md'='md'; '.markdown'='md'; '.mdx'='mdx';
  '.json'='json'
}

function Get-Fence([string]$text) {
  if ($text -notmatch '```') { return '```' }
  elseif ($text -notmatch '````') { return '````' }
  else { return '~~~~' }
}

function Is-ExcludedFileName([string]$name) {
  foreach ($pat in $excludeNamePatterns) {
    if ([System.Management.Automation.WildcardPattern]::new($pat, 'IgnoreCase').IsMatch($name)) { return $true }
  }
  return $false
}

Write-Info "Scanning: $Root"

# Gather files
$files = Get-ChildItem -Path $Root -File -Recurse -ErrorAction SilentlyContinue |
  Where-Object {
    $rel = [IO.Path]::GetRelativePath($Root, $_.FullName)
    $ext = $_.Extension.ToLowerInvariant()
    # Exclude directories
    if ($excludeDirRegex -and ($rel -match $excludeDirRegex)) { return $false }
    # Include by extension or Dockerfile
    $isDocker = ($_.Name -match '^Dockerfile(\..+)?$')
    if (-not $isDocker -and -not ($includeExt -contains $ext)) { return $false }
    # Exclude by name patterns
    if (Is-ExcludedFileName $_.Name) { return $false }
    # Size guard (skip huge files > 5MB)
    if ($_.Length -gt 5MB) { return $false }
    return $true
  } |
  Sort-Object FullName

if (-not $files -or $files.Count -eq 0) {
  Write-Warning "No files found to include. Check filters."
  return
}

Write-Info ("Including {0} files" -f $files.Count)

# Build header and index
$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("# Combined Code Bundle")
$lines.Add("")
$lines.Add(("Generated: {0:yyyy-MM-dd HH:mm:ss K}" -f [DateTimeOffset]::Now))
$lines.Add(("Root: {0}" -f $Root))
$lines.Add(("Files: {0}" -f $files.Count))
$lines.Add("")
$lines.Add("## Index")
foreach ($f in $files) {
  $rel = [IO.Path]::GetRelativePath($Root, $f.FullName)
  $lines.Add("- `" + $rel.Replace('`','``') + "`")
}
$lines.Add("")

# Append each file content with fenced code blocks
foreach ($f in $files) {
  $rel = [IO.Path]::GetRelativePath($Root, $f.FullName)
  $ext = $f.Extension.ToLowerInvariant()
  $lang = if ($f.Name -match '^Dockerfile(\..+)?$') { 'dockerfile' } else { $langMap[$ext] }
  if (-not $lang) { $lang = 'text' }
  Write-Info "Bundling: $rel"

  $content = Get-Content -Path $f.FullName -Raw -Encoding UTF8
  $fence = Get-Fence $content

  $lines.Add("\n---\n")
  $lines.Add("### " + $rel)
  $lines.Add("")
  $lines.Add($fence + $lang)
  $lines.Add($content)
  $lines.Add($fence)
}

# Write output (UTF-8)
$null = New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($Output)) -Force -ErrorAction SilentlyContinue
$lines -join "`n" | Set-Content -Path $Output -Encoding utf8
Write-Info "Wrote: $Output"
```

Notes:

- Edit the `$includeExt`, `$excludeDirs`, and `$excludeNamePatterns` lists in the script to tweak what’s included.
- The script intentionally skips large files (> 5MB), minified assets, lockfiles, images, and binaries.
- `.vscode/*.json` will be included (useful editor configs), while typical build outputs and caches are excluded.

<!-- End file: code.md -->

## codex_instructions.md

<!-- Begin file: codex_instructions.md -->

### Codex: Implement `TODO.md` in Phases

**ROLE & GOAL**

You are an implementation agent. Execute the repository’s `TODO.md` end-to-end in manageable phases with guarded changes, verifiable tests, and clear commits. Work directly in this repo. Produce code, migrations, tests, UI, and docs exactly where they belong. When you finish a phase, stop and present a concise diff summary and next actions.

**GROUND TRUTH**

All requirements, deliverables, and acceptance criteria come from `TODO.md`. Treat it as the single source of truth.

**OPERATING RULES**

1. **Branches & Commits**

   * Create a feature branch per phase: `feat/todo-phase-<n>-<slug>`.
   * Make small, logically grouped commits with meaningful messages.
   * Keep existing project tooling (Makefile, CI, linting) intact.

2. **Compatibility**

   * This codebase runs on Windows dev environments—avoid bash-only assumptions. Provide PowerShell equivalents if you add scripts.
   * Don’t remove existing scripts/targets unless the TODO explicitly requires it.

3. **Tests & CI**

   * Add/extend tests per acceptance criteria. Ensure `make quality` and any Playwright/API/pytest suites pass locally.
   * If CI is configured, wire new checks into existing jobs, not ad-hoc scripts.

4. **Docs**

   * Update any referenced docs in the TODO (OPERATIONS.md, docs/*, README/RELEASE notes). Include rollback/reset notes where called for.

5. **Visibility**

   * After each phase, produce:

     * A brief CHANGELOG entry,
     * A summary of changed files,
     * Any operator steps (e.g., DB migration commands).

---

## PHASE PLAN

### Phase 0 — Discovery & Baseline

* Parse `TODO.md` and confirm repo structure (Next.js app, FastAPI backend, Prisma schema, Playwright/pytest layout, Make targets).
* Run local verification commands (`make db.verify`, `make quality`, existing test suites).
* Output: a short report of current pass/fail and any blockers you’ll resolve within later phases.

### Phase 1 — Glossary Seed & Runbook (TODO §1)

**Implement:**

* Extend `prisma/seed.ts` with deterministic sample entries (`approved`, `pending`, `rejected`) with stable IDs.
* Add `tests/test_seed_manifest.py` validating rows after `make db.seed`.
* Update **OPERATIONS.md** (reset/rollback steps) and **docs/glossary-spec.md** (provisioning + rollback).
  **Accept:** `make db.seed` deterministic; tests green; docs updated.

### Phase 2 — Glossary UX Follow-through (TODO §2)

**Implement:**

* Add Mermaid sequence diagram to `docs/glossary-spec.md`.
* Add ADR links or “Decision Notes” explaining workflow choices; list follow-ups as backlog links.
  **Accept:** Diagram renders; decisions documented.

### Phase 3 — RBAC Integration Coverage (TODO §3)

**Implement:**

* **Playwright:** Non-admin → `/admin` and `/api/glossary` → `403/redirect`; Admin CRUD works.
* **API/route tests:** Next.js route handlers with mocked sessions per role; FastAPI admin endpoints reject with `401/403` when invalid/missing.
* Wire into CI via `make quality` / frontend job.
  **Accept:** Tests fail on RBAC regressions; CI coverage in place.

### Phase 4 — pgvector GUC Bootstrap (TODO §4)

**Implement:**

* Add idempotent migration ensuring `set_config('app.pgvector_lists','100', true)` exists.
* (Optional) Extend `scripts/db_verify.py` to assert/print GUC value.
* Update **OPERATIONS.md** with rollback/override notes.
  **Accept:** Fresh envs pass `make db.verify`.

### Phase 5 — Version Parity Automation (TODO §5)

**Implement:**

* Create `scripts/check_version_parity.py` comparing `VERSION` ↔ `package.json.version`.
* Add `version-check` Make target; include in `quality` (and optionally `verify`).
* Note in `README.md` or `RELEASE.md`.
  **Accept:** CI/local checks fail on drift.

### Phase 6 — Admin Ops Console (Uncertain, Tickets, Glossary) (TODO §6)

**Implement:**

* **UI `/admin`** with tabs: **Uncertain**, **Tickets**, **Glossary**.

  * Uncertain: table (date, user, question, confidence, top sources) + actions (**Approve**, **Ask Follow-up**, **Escalate**).
  * Tickets: list AExxx with status, assignee, last activity.
  * Glossary: search + inline edit (RBAC-gated).
* **API:**

  * `GET /api/admin/uncertain` returns chats with `confidence < CONFIDENCE_THRESHOLD` and `status='pending_review'`.
  * `POST /api/admin/uncertain/:id/approve` marks reviewed (+ reviewer, timestamp).
  * `POST /api/admin/uncertain/:id/escalate` creates/links AE ticket; logs action.
* **DB/Prisma:**

  * `chats`: add `confidence FLOAT`, `status TEXT DEFAULT 'ok'`, `reviewed_by`, `reviewed_at`.
  * `tickets`: ensure `AE id`, `status`, `assignee`, `linked_chat_id`.
* **RBAC:** only `admin` sees `/admin`; `reviewer` limited read/write.
  **Accept:** Role restrictions enforced; actions emit audit events; tests cover 403s.

### Phase 7 — Uncertain Chat Validation Flow (TODO §7)

**Implement:**

* Backend: when `confidence < CONFIDENCE_THRESHOLD`, set `chats.status='pending_review'` and persist `{question, top_k sources, request_id}`.
* Route: `POST /api/admin/uncertain/:id/ask-followup` stores a canonical follow-up prompt.
* UI: review drawer with question, answer, sources, `request_id`; buttons call routes.
* **Playwright**: create low-confidence chat fixture → verify appears → approve → status flips to `reviewed`.
  **Accept:** Flow observable; tests green.

### Phase 8 — Dictionary (Glossary) Update Semantics (TODO §8)

**Implement:**

* API: `PUT /api/glossary/:id` (update) and `POST /api/glossary` (create), both admin-only; upsert on unique `(org_id, term)`.
* Validation: reject empty `term`/`definition`; normalize whitespace; optional `synonyms[]`.
* Auditing: write to `rag_events` (actor, action, glossary_id, before/after).
* UI: inline edit row with optimistic update + toasts.
  **Accept:** No dupes; RBAC enforced; audit row written.

---

## WORKFLOW PER PHASE

1. Create branch `feat/todo-phase-<n>-<slug>`.
2. Implement code/tests/migrations/docs.
3. Run:

   * `make db.migrate` (if migrations),
   * `make db.seed` (if seeds),
   * `make quality` (ensure all suites pass).
4. Produce a brief end-of-phase summary:

   * Files changed, commands to run, notable decisions, any follow-ups.
5. Open a PR (or present diff) titled `TODO Phase <n>: <name>`.

**STOP after each phase** and present the summary and diffs for review before proceeding.

---

**Begin with Phase 0 now.** When ready for Phase 1, present the short baseline report and proceed.

---

<!-- End file: codex_instructions.md -->

## CONTRIBUTING.md

<!-- Begin file: CONTRIBUTING.md -->

# CONTRIBUTING — Atticus

Thank you for contributing to Atticus! This guide explains how to set up your environment, maintain code quality, and keep documentation consistent.

---

## Development Environment

- Use **Python 3.12** and **Node.js 20**.
- Install Python dependencies:
  ```bash
  pip install -U pip pip-tools
  pip-compile -U requirements.in
  pip-sync requirements.txt
  ```
- Install Node dependencies:
  ```bash
  npm install
  ```

---

## Code Quality Workflow

Before committing any change, run:

```bash
make quality         # Ruff + mypy + pytest + Next lint/typecheck/build + audits
npm run format:check # Prettier (with tailwind sorting)
pre-commit run --all-files --show-diff-on-failure
```

Guidelines:

- Maintain >=90% test coverage. Add or update tests for every behaviour change.
- Keep documentation in sync, especially [README.md](README.md), [OPERATIONS.md](OPERATIONS.md), [RELEASE.md](RELEASE.md), and [AGENTS.md](AGENTS.md).
- Use `npm run format` and `make format` to auto-fix style issues before re-running the checks above.

---

## Editor Setup (VS Code + Ruff Native Server)

Atticus ships with a VS Code workspace that enables **Ruff’s native language server** for fast linting and formatting.

- Make sure the VS Code extension `charliermarsh.ruff` is installed (recommended via `.vscode/extensions.json`).
- On save, Ruff automatically organizes imports and fixes style issues.

This setup eliminates the need for `ruff-lsp` and ensures consistent formatting across the team.

---

## Commit Guidelines

- Use **imperative mood** in commit messages (e.g. `fix: correct SMTP config parsing`).
- Include a clear **scope** where relevant (e.g. `ui: add contact route`).
- Reference related issue or task IDs when possible.

---

## Documentation and Cross‑Links

- Keep references between [README.md](README.md), [AGENTS.md](AGENTS.md), and [OPERATIONS.md](OPERATIONS.md) accurate.
- Update [CHANGELOG.md](CHANGELOG.md) if your changes affect users.
- Move completed tasks from [TODO.md](TODO.md) to [TODO_COMPLETE.md](TODO_COMPLETE.md) with date and commit reference.

---

## Submitting Pull Requests

1. Create a feature branch.
2. Run all quality checks and update docs.
3. Submit a pull request with a concise summary of the change.
4. Ensure CI passes linting, typing, and evaluation regression gates before merge.

By following this guide, you’ll help keep Atticus secure, maintainable, and easy for everyone to use.

<!-- End file: CONTRIBUTING.md -->

## docs/api/README.md

<!-- Begin file: docs/api/README.md -->

# API Documentation

## Generating the OpenAPI Schema

Run either command to emit the latest schema:

```bash
make openapi
```

or

```bash
python scripts/generate_api_docs.py --output docs/api/openapi.json
```

The CLI loads the FastAPI application directly, so the server does not need to be running.

---

## `/ask` Request & Response

```jsonc
POST /ask
{
  "question": "How does Atticus escalate low confidence answers?",
  "models": ["C7070"],
  "filters": {
    "source_type": "runbook"
  }
}
```

- `question` (string, required) - Natural-language query. Alias `query` is also accepted for backwards compatibility.
- `filters` (object, optional) - Restrict retrieval. Supported keys: `source_type`, `path_prefix`.
- `models` (array, optional) - Explicit model or family identifiers returned from a clarification prompt. When omitted Atticus infers models from the question text.

```jsonc
200 OK
{
  "answer": "Atticus blends retrieval and LLM confidence...",
  "answers": [
    {
      "model": "Apeos C7070",
      "family": "C7070",
      "family_label": "Apeos C7070 range",
      "answer": "Atticus blends retrieval and LLM confidence...",
      "confidence": 0.74,
      "should_escalate": false,
      "sources": [
        {
          "chunkId": "chunk-000045",
          "path": "content/20240901_escalation_playbook_v1.pdf",
          "page": 7,
          "heading": "Escalation Workflow",
          "score": 0.82
        }
      ]
    }
  ],
  "confidence": 0.74,
  "should_escalate": false,
  "request_id": "9db0dd1c-...",
  "sources": [
    {
      "chunkId": "chunk-000045",
      "path": "content/20240901_escalation_playbook_v1.pdf",
      "page": 7,
      "heading": "Escalation Workflow",
      "score": 0.82
    }
  ]
}
```

- `answer` - Aggregate response (string). For multi-model queries each entry in `answers` contains the scoped answer.
- `answers` - List of per-model responses surfaced when multiple models or families are requested.
- `sources` - Aggregated supporting citations for the response (per-entry sources live under each `answers[i].sources`).
- `confidence` - Combined retrieval plus LLM score (0-1).
- `should_escalate` - `true` when `confidence` falls below `CONFIDENCE_THRESHOLD`.
- `request_id` - Trace identifier surfaced in logs.

When Atticus cannot confidently infer a model, the endpoint returns a clarification payload instead of an answer:

```jsonc
200 OK
{
  "request_id": "bcf8854e-...",
  "clarification": {
    "message": "Which model are you referring to? If you like, I can provide a list of product families that I can assist with.",
    "options": [
      { "id": "C7070", "label": "Apeos C7070 range" },
      { "id": "C8180", "label": "Apeos C8180 series" }
    ]
  }
}
```

Errors follow the JSON error schema described in [AGENTS.md](../AGENTS.md#error-handling).

---

## Related References

- [ATTICUS_DETAILED_GUIDE.md](../ATTICUS_DETAILED_GUIDE.md)
- [README.md](../README.md)
- [OPERATIONS.md](../OPERATIONS.md)

<!-- End file: docs/api/README.md -->

## docs/ATTICUS_DETAILED_GUIDE.md

<!-- Begin file: docs/ATTICUS_DETAILED_GUIDE.md -->

# Atticus Detailed Guide

## Model Name Disambiguation

1. **Direct questions** — detect precise model mentions (for example, "Apeos C4570"), scope retrieval to the matching family, and return a single answer with citations limited to that family.
2. **Unclear questions** — when parser confidence drops below the clarification threshold, respond with a `clarification` payload listing the available families and delay retrieval until the UI resubmits the original question with selected `models`.
3. **Multi-model questions** — if several models are present ("C4570 and C6580"), fan out retrieval per model and return `answers[]`, ensuring each answer carries its own `sources` while preserving the aggregated `sources` array for consumers that expect it.
4. **Follow-up flow** — UI buttons post the original prompt with `models` populated from the selected family so downstream logging and escalations have explicit model scope.

See `tests/test_model_parser.py`, `tests/test_retrieval_filters.py`, `tests/test_chat_route.py`, `tests/test_ui_route.py`, and `tests/playwright/chat.spec.ts` for executable examples.

<!-- End file: docs/ATTICUS_DETAILED_GUIDE.md -->

## docs/glossary-spec.md

<!-- Begin file: docs/glossary-spec.md -->

# Glossary Specification

The glossary module enables reviewers to propose terminology updates and administrators
to approve or reject entries. The workflow is designed to mirror the RBAC policies in the
Next.js admin UI and Prisma models.

## Roles

| Role       | Permissions                                                |
| ---------- | ---------------------------------------------------------- |
| `user`     | Read-only access to approved glossary entries.             |
| `reviewer` | Submit new terms and propose edits.                        |
| `admin`    | Approve/reject proposals, manage history, export glossary. |

## Data Model

```prisma
model GlossaryEntry {
  id           String          @id @default(cuid())
  term         String
  definition   String          @db.Text
  synonyms     String[]        @default([])
  status       GlossaryStatus  @default(PENDING)
  orgId        String
  org          Organization    @relation(fields: [orgId], references: [id], onDelete: Cascade)
  authorId     String
  author       User            @relation("GlossaryAuthor", fields: [authorId], references: [id])
  updatedById  String?
  updatedBy    User?           @relation("GlossaryUpdatedBy", fields: [updatedById], references: [id])
  reviewerId   String?
  reviewer     User?           @relation("GlossaryReviewer", fields: [reviewerId], references: [id])
  reviewNotes  String?         @db.Text
  reviewedAt   DateTime?
  events       RagEvent[]
  createdAt    DateTime        @default(now())
  updatedAt    DateTime        @updatedAt

  @@unique([orgId, term])
  @@index([orgId, status])
}
```

All mutations emit structured `RagEvent` audit rows (mirrored in `logs/app.jsonl`) including the acting user,
the request/trace ID, and the state transition. Row-level security is enforced through
Prisma queries executed inside `withRlsContext` and mirrored on the FastAPI admin APIs via
the `X-Admin-Token` header.

## API Contracts

- `GET /api/glossary` – reviewer/admin session required; returns serialized entries with
  author/reviewer metadata.
- `POST /api/glossary` – admin session required; idempotent upsert keyed by `(orgId, term)` that accepts term, definition, synonyms, and status updates while recording author/reviewer metadata and request IDs.
- `PUT /api/glossary/:id` – admin session required; updates an entry in place (definition, synonyms, status, review notes) and stamps reviewer metadata when a decision is made.
- FastAPI `/admin/dictionary` endpoints mirror the glossary state for legacy tooling and
  require a matching `X-Admin-Token` header; failures emit contract-compliant error
  payloads with `request_id` for observability.

## UI Flow

1. Reviewer submits a new term with synonyms and rationale.
2. Admin views pending proposals on `/admin/glossary`, edits definitions inline, captures review notes, and approves.
3. Approved entries become available to all users and propagate via the API contract, with each change mirrored in `RagEvent` history.

### Sequence Diagram

```mermaid
sequenceDiagram
  participant Reviewer
  participant Admin
  participant System
  Reviewer->>Admin: Submit glossary entry
  Admin->>System: Approve/Reject
  System-->>Reviewer: Status update + audit log
```

### Decision Notes

- **Single admin review gate** keeps quality control centralized and aligns with our RBAC policy where only admins can approve or
  reject terms. This mirrors the Prisma ownership model and prevents conflicting reviewer decisions.
- **Audit-first feedback** relies on structured events written during each transition so downstream services can reconcile glossary
  changes without polling Prisma directly.
- **FastAPI bridge retained** to support legacy tooling that still depends on the `/admin/dictionary` endpoints during the migration
  period.

### Follow-ups

- Reviewer/admin notifications for status changes remain open in the backlog — tracked in [TODO.md §5](../TODO.md#5-uncertain-chat-validation-flow).
- Dedicated audit UI enhancements live under [TODO.md §4](../TODO.md#4-admin-ops-console-uncertain-chats-tickets-glossary) alongside the combined admin console workstream.

## Seed Data & Provisioning

- `make db.seed` provisions:
  - Organization `org-atticus` (overridable via `DEFAULT_ORG_ID`).
  - Service users `glossary.author@seed.atticus` (reviewer) and `glossary.approver@seed.atticus` (admin) for deterministic RBAC checks.
  - Three glossary rows covering the primary workflow states:
    - `glossary-entry-managed-print-services` → **APPROVED** with reviewer metadata for smoke tests.
    - `glossary-entry-proactive-maintenance` → **PENDING** awaiting admin action.
    - `glossary-entry-toner-optimization` → **REJECTED** with notes capturing why it failed review.
- Re-running the seed is idempotent: each entry is upserted by stable IDs and the reviewer/author assignments are refreshed.
- Override defaults (organization name, admin bootstrap account, etc.) by exporting `DEFAULT_ORG_NAME`, `ADMIN_EMAIL`, and `ADMIN_NAME` before invoking the target.

## Reset & Rollback

- To reset the glossary to the deterministic baseline:
  1. `make db.seed` — reruns Prisma seeding and restores the canonical entries.
  2. Confirm via `pytest tests/test_seed_manifest.py::test_glossary_seed_entries_round_trip` (requires a reachable Postgres instance).
- To restore production data after testing seeds:
  1. Snapshot `GlossaryEntry` rows (e.g., `COPY "GlossaryEntry" TO STDOUT WITH CSV HEADER`).
  2. After validation, re-import using `COPY ... FROM STDIN` or Prisma scripts, then rerun `make db.seed` to ensure support accounts persist.
- Rollbacks should always re-run `make db.seed` so the deterministic reviewers remain available for smoke suites.

### Sequence Diagram

```mermaid
sequenceDiagram
  participant Reviewer
  participant Admin
  participant System
  Reviewer->>Admin: Submit glossary entry
  Admin->>System: Approve/Reject
  System-->>Reviewer: Status update + audit log
```

### Decision Notes

- **Single admin review gate** keeps quality control centralized and aligns with our RBAC policy where only admins can approve or
  reject terms. This mirrors the Prisma ownership model and prevents conflicting reviewer decisions.
- **Audit-first feedback** relies on structured events written during each transition so downstream services can reconcile glossary
  changes without polling Prisma directly.
- **FastAPI bridge retained** to support legacy tooling that still depends on the `/admin/dictionary` endpoints during the migration
  period.

### Follow-ups

- Reviewer/admin notifications for status changes remain open in the backlog — tracked in [TODO.md §5](../TODO.md#5-uncertain-chat-validation-flow).
- Dedicated audit UI enhancements live under [TODO.md §4](../TODO.md#4-admin-ops-console-uncertain-chats-tickets-glossary) alongside the combined admin console workstream.

## Seed Data & Provisioning

- `make db.seed` provisions:
  - Organization `org-atticus` (overridable via `DEFAULT_ORG_ID`).
  - Service users `glossary.author@seed.atticus` (reviewer) and `glossary.approver@seed.atticus` (admin) for deterministic RBAC checks.
  - Three glossary rows covering the primary workflow states:
    - `glossary-entry-managed-print-services` → **APPROVED** with reviewer metadata for smoke tests.
    - `glossary-entry-proactive-maintenance` → **PENDING** awaiting admin action.
    - `glossary-entry-toner-optimization` → **REJECTED** with notes capturing why it failed review.
- Re-running the seed is idempotent: each entry is upserted by stable IDs and the reviewer/author assignments are refreshed.
- Override defaults (organization name, admin bootstrap account, etc.) by exporting `DEFAULT_ORG_NAME`, `ADMIN_EMAIL`, and `ADMIN_NAME` before invoking the target.

## Reset & Rollback

- To reset the glossary to the deterministic baseline:
  1. `make db.seed` — reruns Prisma seeding and restores the canonical entries.
  2. Confirm via `pytest tests/test_seed_manifest.py::test_glossary_seed_entries_round_trip` (requires a reachable Postgres instance).
- To restore production data after testing seeds:
  1. Snapshot `GlossaryEntry` rows (e.g., `COPY "GlossaryEntry" TO STDOUT WITH CSV HEADER`).
  2. After validation, re-import using `COPY ... FROM STDIN` or Prisma scripts, then rerun `make db.seed` to ensure support accounts persist.
- Rollbacks should always re-run `make db.seed` so the deterministic reviewers remain available for smoke suites.

## CI Expectations

- `make test.api` exercises glossary endpoints under auth.
- `make quality` runs Prisma client type checks, Vitest RBAC unit tests, and Playwright admin flows to guard glossary access.
- Seed data for glossary lives alongside the CED seed manifest (`make seed`).

<!-- End file: docs/glossary-spec.md -->

## docs/README.md

<!-- Begin file: docs/README.md -->

# Atticus Documentation

## Adding New Content

1. Place documents inside the `content/` tree following the taxonomy in
   `AGENTS.md` §3.1.
2. Name files using `YYYYMMDD_topic_version.ext` for traceability.
3. Run `python scripts/ingest_cli.py` (or `make ingest`) to parse, chunk
   (defaults controlled by `config.yaml` / `.env`), embed, and update the
   index.
4. Review the ingestion report in `logs/app.jsonl` and commit the updated index
   snapshot plus `indices/manifest.json`.
5. Execute the evaluation harness with
   `python scripts/eval_run.py --json --output-dir eval/runs/manual` to confirm
   retrieval quality before tagging a release.
6. Regenerate API documentation with `python scripts/generate_api_docs.py` so
   the OpenAPI schema in `docs/api/openapi.json` stays in sync with the
   deployed code.

<!-- End file: docs/README.md -->

## docs/REMOTE_ACCESS.md

<!-- Begin file: docs/REMOTE_ACCESS.md -->

# REMOTE ACCESS - Atticus

This guide explains how to reach a local Atticus instance from another PC without exposing the machine to
the internet. It presents three supported approaches so you can choose the level of automation, security,
and tooling that fits your environment.

---

## Quick Decision Matrix

| Option                 | Best For                                          | Security Posture                                            | What You Need                                              |
| ---------------------- | ------------------------------------------------- | ----------------------------------------------------------- | ---------------------------------------------------------- |
| **Tailscale**          | Always-on secure mesh between office/home devices | Zero-trust, device-based auth, automatic key rotation       | Personal/enterprise Tailscale account (free tier works)    |
| **Cloudflare Tunnel**  | Sharing access with vendors or short-term demos   | One-time tokens, granular routes, no inbound firewall rules | Cloudflare account with a free zone + `cloudflared` binary |
| **SSH Reverse Tunnel** | One-off troubleshooting from a trusted jump host  | Depends on SSH key hygiene                                  | Any VPS or machine reachable from the remote PC            |

---

## Option 1 - Tailscale (Recommended)

1. Install Tailscale on the Atticus host and the remote PC: <https://tailscale.com/download>.
2. Authenticate each device with the same account (or organization SSO).
3. Tag the Atticus host (optional but recommended) with `atticus-server` to simplify ACLs.
4. Start Atticus locally:

   ```bash
   make api
   ```

5. Connect from the remote PC using the Tailscale IP shown in the admin console:

   ```bash
   # Example assuming the host advertises 100.101.102.103
   curl http://100.101.102.103:8000/health
   ```

6. Lock down access with an ACL snippet:

   ```json
   {
     "ACLs": [
       {
         "Action": "accept",
         "Users": ["group:sales", "user:you@example.com"],
         "Ports": ["tag:atticus-server:8000"]
       }
     ]
   }
   ```

**Pros**: 2-minute setup, device-level revocation, auto-generated DNS names like
`atticus-hostname.tailnet.ts.net`.

**Cons**: Requires installing the client on every participating machine.

---

## Option 2 - Cloudflare Tunnel

1. Install `cloudflared` on the Atticus host:

   ```powershell
   winget install Cloudflare.cloudflared
   ```

2. Authenticate and select the zone that will front your tunnel (e.g. `yourcompany.com`):

   ```bash
   cloudflared login
   ```

3. Create a dedicated tunnel:

   ```bash
   cloudflared tunnel create atticus-local
   ```

4. Route a DNS record to the tunnel:

   ```bash
   cloudflared tunnel route dns atticus-local atticus.yourcompany.com
   ```

5. Run the connector while Atticus is active:

   ```bash
   make api &
   cloudflared tunnel run --url http://localhost:8000 atticus-local
   ```

6. Protect access with Cloudflare Access (SSO, one-time PINs, or service tokens).

**Pros**: No inbound firewall rules, audited access logs, granular policies per path.

**Cons**: Outbound tunnel must stay alive; run it as a service for long-lived usage.

---

## Option 3 - SSH Reverse Tunnel (Minimal Dependencies)

1. Pick a jump host reachable from the remote PC (a lightweight VPS works).
2. Create an SSH key for the Atticus host and add it to the jump host `authorized_keys`.
3. Start the tunnel from the Atticus host:

   ```bash
   ssh -N -R 18080:localhost:8000 user@jump-host.example.com
   ```

4. From the remote PC, connect to the jump host and forward traffic locally:

   ```bash
   ssh -L 8000:localhost:18080 user@jump-host.example.com
   ```

5. Visit `http://localhost:8000` on the remote PC—traffic traverses the secure SSH tunnel.

**Pros**: Uses built-in tooling; no extra accounts required.

**Cons**: You must maintain the intermediate host and manage SSH keys carefully.

---

## Operational Checklist

- Treat every remote-access path as production: use MFA, rotate credentials, and log access.
- Update `.env` with `ALLOWED_ORIGINS` if you front Atticus with a different hostname (CORS).
- Enable `LOG_VERBOSE=1` during rollout so access logs capture remote IPs.
- Tear down tunnels when demos finish to avoid orphaned exposure.

---

## Related Documents

- [OPERATIONS.md](OPERATIONS.md) - runbooks, evaluation workflow, and rollback steps.
- [SECURITY.md](SECURITY.md) - IAM, SES policies, and secrets guidance.
- [README.md](README.md) - setup instructions and Make targets.

<!-- End file: docs/REMOTE_ACCESS.md -->

## docs/runbooks/auth-rbac.md

<!-- Begin file: docs/runbooks/auth-rbac.md -->

# Auth & RBAC Runbook

This runbook documents the Auth.js + Prisma deployment that powers Atticus phase 3.

## Overview

- **Provider**: Auth.js (NextAuth) with email magic link.
- **Adapter**: Prisma + Postgres with row-level security (RLS) keyed by `org_id` and role.
- **Roles**: `USER`, `REVIEWER`, `ADMIN`.
  - Users and reviewers can read glossary entries scoped to their org.
  - Admins can invite teammates, promote glossary entries, and manage roles.
- **Session storage**: Database-backed sessions (`Session` table) with Prisma adapter.

## Environment variables

| Variable                                                                                  | Purpose                                                                         |
| ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| `DATABASE_URL`                                                                            | Postgres connection string used by Prisma and Auth.js.                          |
| `AUTH_SECRET`                                                                             | Random string used to sign NextAuth cookies/JWT.                                |
| `DEFAULT_ORG_ID` / `DEFAULT_ORG_NAME`                                                     | Seed organization for default tenancy.                                          |
| `ADMIN_EMAIL` / `ADMIN_NAME`                                                              | Bootstrap admin account created by `npm run db:seed`.                           |
| `EMAIL_SERVER_HOST` / `EMAIL_SERVER_PORT` / `EMAIL_SERVER_USER` / `EMAIL_SERVER_PASSWORD` | SMTP server used for magic link delivery.                                       |
| `EMAIL_FROM`                                                                              | From address for Auth.js email provider.                                        |
| `AUTH_DEBUG_MAILBOX_DIR`                                                                  | Filesystem directory where test magic links are persisted (used by Playwright). Defaults to `./logs/mailbox`. |

Use `python scripts/generate_env.py --force` to regenerate `.env` with sensible defaults. Override secrets in production.

## Provisioning steps

1. **Start Postgres**
   ```bash
   make db.up
   ```
2. **Apply migrations**
   ```bash
   make db.migrate
   ```
3. **Generate Prisma client**
   ```bash
   npm run prisma:generate
   ```
4. **Seed default org + admin**
   ```bash
   make db.seed
   ```
   The seed script creates (or updates) the organization referenced by `DEFAULT_ORG_ID` and promotes `ADMIN_EMAIL` to `ADMIN`.
5. **Run the app**
   ```bash
   npm run dev
   ```
   Visit `http://localhost:3000/signin`, request a magic link for the admin email, and open the link to access `/admin`.

## Testing

- **Unit**: `npm run test:unit` (Vitest) covers RBAC helpers.
- **Playwright**: `npm run test:e2e` validates the magic link flow and admin gating. Ensure the dev server is running and `AUTH_DEBUG_MAILBOX_DIR` (default `./logs/mailbox`) is writable before running.
- **Smoke**: `make web-test` + `make web-e2e` are wired into CI.

## RLS behaviour

- Policies enforce `org_id` scoping for users, sessions, accounts, and glossary entries.
- Admin-only actions (`INSERT`, `UPDATE`, `DELETE` on `GlossaryEntry`) require the connection role to be `ADMIN`. Service-level operations (NextAuth adapter) run under the `SERVICE` context, set via database defaults, to bootstrap new sessions.
- Always wrap Prisma calls that rely on user context with `withRlsContext(session, fn)` to set `app.current_user_*` settings.

## Operations

- **Magic link debugging**: Magic links are written to `<email>.txt` in `AUTH_DEBUG_MAILBOX_DIR` (default `./logs/mailbox`). Clear the file to invalidate previous links.
- **Role changes**: Use Prisma Studio or a SQL client to update `User.role`. RLS allows admins to self-manage via future UI.
- **Glossary management**: Admins manage terms in `/admin`. Reviewers will gain propose-only permissions in later phases.

## Rollback

1. Stop the Next.js app (`Ctrl+C`).
2. Revert migrations by restoring the previous database snapshot or running `psql` to drop the new tables/enums if safe.
3. Reset the workspace by checking out the prior git tag and reinstalling dependencies (`npm install`).
4. Restore `.env` from backups and restart services.

For emergency disablement, set `NEXTAUTH_SECRET` to an empty value and restart; Auth.js rejects new sessions, effectively putting the UI into maintenance mode while RBAC policies remain intact.

<!-- End file: docs/runbooks/auth-rbac.md -->

## IMPLEMENTATION_PLAN.md

<!-- Begin file: IMPLEMENTATION_PLAN.md -->

# Implementation Plan — Atticus RAG Consistency Cleanup

| Phase   | Status | Notes                                                                               |
| ------- | ------ | ----------------------------------------------------------------------------------- |
| Phase 0 | ✅     | [6e50c78](commit/6e50c78) – audit tooling dependencies installed                    |
| Phase 1 | ✅     | [HEAD](commit/HEAD) – Prisma vector schema + pgvector verification wired            |
| Phase 2 | ✅     | [HEAD](commit/HEAD) – `/api/ask` contract unified with SSE client + tests           |
| Phase 3 | ✅     | [HEAD](commit/HEAD) – Glossary workflow hardened with review metadata and RBAC docs |
| Phase 4 | ✅     | [HEAD](commit/HEAD) – Frontend hygiene complete                                     |
| Phase 5 | ✅     | [HEAD](commit/HEAD) – Legacy UI archived & structure updated                        |
| Phase 6 | ✅     | [HEAD](commit/HEAD) – Developer tooling + CI harmonized                             |
| Phase 7 | ✅     | [HEAD](commit/HEAD) – Documentation + release sync complete                         |

This plan sequences remediation work uncovered in `AUDIT_REPORT.md` and merges active TODOs. Each phase lists required commits, commands (POSIX + PowerShell where relevant), acceptance criteria, and cross-references to TODO items.

> **Note:** Legacy references to `TODO` sections map to the consolidated backlog in [TODO.md](TODO.md).

## Phase 0 – Safety, Branching, and Baseline Artifacts

- **Objectives**
  - Create working branch `audit/rag-consistency-cleanup`.
  - Ensure `.env.example` covers all required settings before touching secrets (extends TODO §A.1).
  - Capture dependency baselines and enable new audit scripts.
- **Commits**
  - `chore(phase-0): scaffold audit automation and env template`
- **Key Tasks**
  - Copy `.env.example` → `.env` locally; verify `scripts/generate_env.py` parity.
  - Run `npm install`, `pip-sync requirements.txt` (POSIX) / `python -m pip install -r requirements.txt` (PowerShell) to capture lockfile state.
  - Document any failing installs in TROUBLESHOOTING.md (links to TODO §A.4).
- **Commands**
  - POSIX: `git checkout -b audit/rag-consistency-cleanup`
  - PowerShell: `git checkout -b audit/rag-consistency-cleanup`
- **Acceptance Criteria**
  - Branch created, `.env` generated without manual edits.
  - Audit scripts executable (`npm run audit:ts`, `python scripts/audit_unused.py`).

## Phase 1 – Data Layer First (TODO §A.3, §A.4, §D.4)

- **Objectives**
  - Model pgvector schema via Prisma; align Python + Prisma migrations.
  - Add `scripts/verify_pgvector.sql` checks to CI + docs.
- **Commits**
  - `feat(phase-1): align prisma schema with pgvector tables`
  - `chore(phase-1): add pgvector verification script and docs`
- **Key Tasks**
  - Extend `prisma/schema.prisma` with vector tables/indexes (`atticus_chunks`, `atticus_documents`).
  - Create migration enabling `CREATE EXTENSION vector`, IVFFlat index, and default probes (ties to TODO §A.3 and FND-006).
  - Update `requirements.in`/`pyproject.toml` notes around `psycopg[binary]` (TODO §D.4).
  - Wire verification SQL into Makefile + CI.
- **Commands**
  - POSIX: `npm run db:migrate`, `psql $DATABASE_URL -f scripts/verify_pgvector.sql`
  - PowerShell: `psql $env:DATABASE_URL -f scripts/verify_pgvector.sql`
- **Acceptance Criteria**
  - Prisma migration applies cleanly on empty DB and existing dev DB.
  - `scripts/verify_pgvector.sql` returns success; Make/CI step added.

## Phase 2 – RAG Contract Unification (TODO §D.2)

- **Objectives**
  - Provide single `/api/ask` endpoint returning `{answer, sources, confidence, request_id, should_escalate}`.
  - Introduce shared DTOs for TypeScript + Python, with typed fetch layer.
- **Commits**
  - `feat(phase-2): unify ask contract across api and app`
  - `test(phase-2): cover ask contract from Next app`
- **Key Tasks**
  - Implement `app/api/ask/route.ts` or proxy to FastAPI with SSE support.
  - Refactor `api/routes/chat.py` to share dataclasses/validators; ensure same schema.
  - Update Next chat surface to call API, handle streaming, log `request_id` (FND-003/FND-007).
  - Add Vitest + pytest coverage verifying contract.
- **Commands**
  - POSIX: `npm run test:unit`, `pytest tests/test_chat_route.py`
  - PowerShell: `npm run test:unit`, `pytest tests/test_chat_route.py`
- **Acceptance Criteria**
  - Contract identical in TypeScript types and Pydantic schema.
  - Chat UI renders streaming responses with sources + error handling.

## Phase 3 – Auth & RBAC Hardening (TODO §B.2, §C.1)

- **Objectives**
  - Finalize Prisma schema for glossary workflow, enforce RBAC across server actions.
  - Document provisioning, tests, and rollback steps.
- **Commits**
  - `feat(phase-3): harden glossary admin workflows`
  - `docs(phase-3): update auth runbooks`
- **Key Tasks**
  - Finish Glossary admin propose/review/approve flow (TODO §B.2, §C.1).
  - Add middleware tests ensuring non-admins blocked (Next + FastAPI).
  - Update TROUBLESHOOTING.md with Auth.js issues (TODO §A.4).
- **Commands**
  - POSIX: `npm run test:e2e`, `pytest tests/test_admin_route.py`
  - PowerShell: `npm run test:e2e`, `pytest tests/test_admin_route.py`
- **Acceptance Criteria**
  - Admin panel fully functional, RBAC enforced server-side.
  - Docs include Windows-friendly auth smoke steps.

## Phase 4 – Frontend Hygiene (TODO §A.1, FND-001/002/007)

- **Objectives**
  - Align Tailwind content paths, remove unused animations, integrate Framer Motion intentionally or remove.
  - Normalize shadcn/ui component usage, ensure Lucide imports tree-shaken.
- **Commits**
  - `refactor(phase-4): consolidate ui components`
  - `style(phase-4): prune legacy tailwind artefacts`
- **Key Tasks**
  - Remove `web/static` (archive if needed) and migrate interactions into Next pages.
  - Adopt shadcn/ui primitives for form controls and table (Glossary panel).
  - Add Framer Motion variants if keeping dependency; otherwise drop.
  - Update Tailwind config to cover new paths (e.g., `lib`, `content`, `docs` if needed).
- **Commands**
  - POSIX: `npm run lint`, `npm run build`
  - PowerShell: `npm run lint`, `npm run build`
- **Acceptance Criteria**
  - `npm run audit:ts` passes with no unused components.
  - Tailwind build has no purge misses; UI uses consistent design tokens.

## Phase 5 – Orphans & Structure Cleanup (TODO §D.1, §D.3)

- **Objectives**
  - Remove FastAPI UI vestiges, restructure repo to separate frontend/back-end clearly.
- **Commits**
  - `refactor(phase-5): remove fastapi ui remnants`
  - `docs(phase-5): align architecture diagrams`
- **Key Tasks**
  - Update `ARCHITECTURE.md` diagrams and AGENTS with new structure (TODO §A.2, §D.5).
  - Drop `api/routes/chat.py` duplication once Next handles ask flow, or vice versa per decision.
  - Update Make targets removing `ui` alias to `npm run dev` once Next is canonical.
- **Commands**
  - POSIX: `make help`
  - PowerShell: `make help`
- **Acceptance Criteria**
  - No orphaned routes/components flagged by `npm run audit:ts` or `python scripts/audit_unused.py`.
  - Repo tree matches updated `REPO_STRUCTURE.md`.

## Phase 6 – Developer Experience & CI (TODO §B.1)

- **Objectives**
- Harmonize linting/formatting (ESLint, Prettier, Ruff formatter, mypy) and ensure CI runs frontend + backend gates.
- **Commits**
  - `chore(phase-6): extend ci matrix for web stack`
  - `chore(phase-6): tighten lint/typecheck configs`
- **Key Tasks**
  - Add ESLint config for shadcn/ui, enable Prettier/biome or confirm formatting strategy.
  - Update GitHub Actions to run `npm run lint`, `npm run typecheck`, `npm run build` on Node 20 matrix with Postgres service.
  - Integrate audit scripts into CI (knip, route audit, vulture) and surface reports as artifacts.
  - Address `npm audit` vulnerabilities or document exceptions.
- **Commands**
  - POSIX: `npm run lint`, `npm run typecheck`, `npm run build`, `python -m pytest`
  - PowerShell: same commands.
- **Acceptance Criteria**
  - CI green with combined Node + Python jobs.
  - Pre-commit hooks cover Ruff, mypy, ESLint, Prettier.

## Phase 7 – Documentation Sync & Release (TODO §A.1–§A.5, §B.1)

- **Objectives**
  - Rewrite README/ARCHITECTURE/OPERATIONS/TROUBLESHOOTING/REQUIREMENTS to match final stack.
  - Update AGENTS.md with resolved conflicts, escalate instructions, and CI gates.
  - Publish release notes & upgrade guidance per semantic version policy.
- **Commits**
  - `docs(phase-7): refresh product documentation`
  - `release(phase-7): bump version and changelog`
- **Key Tasks**
  - Complete outstanding items documented in [TODO.md](TODO.md); move finished tasks to `TODO_COMPLETE.md`.
  - Add upgrade/rollback steps to README + RELEASE.md (per universal backlog instructions).
  - Provide Windows PowerShell equivalents for all scripts/make invocations.
- **Commands**
  - POSIX: `git tag vX.Y.Z`
  - PowerShell: `git tag vX.Y.Z`
- **Acceptance Criteria**
  - [TODO.md](TODO.md) reflects only new/remaining work; duplicates removed.
  - `CHANGELOG.md` documents release with version synced across packages.
  - README accurately describes Next.js + FastAPI hybrid deployment.

## Cross-Phase Considerations

- **Observability**: Introduce metrics dashboards/log shipping in Phases 2–3 when RAG contract and auth are stable.
- **Testing**: Maintain ≥90% backend coverage and add Vitest/Playwright coverage >80% for UI flows.
- **Versioning**: Adopt single `VERSION` file updated in Phase 7; reference from Python/Node builds.
- **Risk Mitigation**: For destructive deletions (e.g., `web/static`), move to `archive/legacy-ui/` first, update documentation, and remove once parity confirmed.

## Notes

- Phase 2 introduced the shared Ask DTOs (`lib/ask-contract.ts`), streaming proxy (`app/api/ask/route.ts`), and Vitest coverage for SSE parsing.
- Phase 3 extended the glossary schema with synonyms/review metadata, updated the admin UI for approvals, and documented Windows-friendly auth + SSE troubleshooting.

<!-- End file: IMPLEMENTATION_PLAN.md -->

## OPERATIONS.md

<!-- Begin file: OPERATIONS.md -->

# OPERATIONS — Atticus

This document provides **day‑to‑day runbooks** and a detailed guide for interpreting evaluation metrics.
It complements [README.md](README.md) for setup and [AGENTS.md](AGENTS.md) for architecture.

---

## Ingest & Index

1. Add or update source files under `content/` using `YYYYMMDD_topic_version.ext` naming.
2. Run ingestion:

   ```bash
   make ingest
   ```

   This parses, chunks (CED policy with SHA-256 dedupe), embeds, and updates the vector index.

3. Check logs in `logs/app.jsonl` for document counts, chunk totals, and token ranges.
4. When ready for release, commit the updated `indices/` snapshot and `indices/manifest.json`.
5. Generate a deterministic seed manifest (for CI smoke tests) via `make seed` and archive `seeds/seed_manifest.json` as needed.

---

## Database Health (pgvector)

Run these checks after applying Prisma migrations or when diagnosing ingestion anomalies.

1. Ensure Docker Compose Postgres is running (`make db.up`).
2. Validate the schema, pgvector extension, and IVFFlat index configuration:

   ```bash
   make db.verify
   ```

   ```powershell
   make db.verify
   ```

   The target wraps `psql "$DATABASE_URL" -v expected_pgvector_dimension=${PGVECTOR_DIMENSION:-3072} -v expected_pgvector_lists=${PGVECTOR_LISTS:-100} -f scripts/verify_pgvector.sql`.
   Override the defaults by exporting `PGVECTOR_DIMENSION` / `PGVECTOR_LISTS` before invoking the command.

3. For ad-hoc checks, run the SQL script directly:

   ```bash
   psql "$DATABASE_URL" -v expected_pgvector_dimension=${PGVECTOR_DIMENSION:-3072} -v expected_pgvector_lists=${PGVECTOR_LISTS:-100} -f scripts/verify_pgvector.sql
   ```

   ```powershell
   if (-not $env:PGVECTOR_DIMENSION) { $env:PGVECTOR_DIMENSION = 3072 }
   if (-not $env:PGVECTOR_LISTS) { $env:PGVECTOR_LISTS = 100 }
   psql "$env:DATABASE_URL" -v expected_pgvector_dimension=$env:PGVECTOR_DIMENSION -v expected_pgvector_lists=$env:PGVECTOR_LISTS -f scripts/verify_pgvector.sql
   ```

   The script fails fast if the extension is missing, the embedding dimension drifts, the IVFFlat index loses its cosine lists configuration, or the `app.pgvector_lists` GUC is unset/mismatched.

   > Requires the `psql` client (`postgresql-client` on Debian/Ubuntu).

4. The migration `20251019090000_pgvector_lists_guc` sets `ALTER DATABASE … SET app.pgvector_lists = '100'`. Override the default by running `ALTER DATABASE <db> SET app.pgvector_lists = '<lists>'` prior to deployments if you require different IVFFlat list counts, then re-run `make db.verify` to confirm.

---

## Glossary Baseline & Rollback

Use these steps to keep glossary fixtures deterministic across environments.

1. Seed the database:

   ```bash
   make db.seed
   ```

   ```powershell
   make db.seed
   ```

   The target provisions service users (`glossary.author@seed.atticus`, `glossary.approver@seed.atticus`) and three glossary entries spanning `APPROVED`, `PENDING`, and `REJECTED` states.

2. Verify the baseline rows (requires Postgres access):

   ```bash
   pytest tests/test_seed_manifest.py::test_glossary_seed_entries_round_trip
   ```

   ```powershell
   pytest tests/test_seed_manifest.py::test_glossary_seed_entries_round_trip
   ```

3. To reset production data after exploratory edits:

   - Snapshot current entries: `psql "$DATABASE_URL" -c 'COPY "GlossaryEntry" TO STDOUT WITH CSV HEADER' > glossary_backup.csv`.
   - Re-import when ready: `psql "$DATABASE_URL" -c "\copy \"GlossaryEntry\" FROM 'glossary_backup.csv' WITH CSV HEADER"`.
   - Rerun `make db.seed` to restore deterministic reviewer accounts.

Document deviations (e.g., temporary reviewer overrides) in the incident or release notes and update `docs/glossary-spec.md` if the workflow changes.

---

## Glossary Baseline & Rollback

Use these steps to keep glossary fixtures deterministic across environments.

1. Seed the database:

   ```bash
   make db.seed
   ```

   ```powershell
   make db.seed
   ```

   The target provisions service users (`glossary.author@seed.atticus`, `glossary.approver@seed.atticus`) and three glossary entries spanning `APPROVED`, `PENDING`, and `REJECTED` states.

2. Verify the baseline rows (requires Postgres access):

   ```bash
   pytest tests/test_seed_manifest.py::test_glossary_seed_entries_round_trip
   ```

   ```powershell
   pytest tests/test_seed_manifest.py::test_glossary_seed_entries_round_trip
   ```

3. To reset production data after exploratory edits:

   - Snapshot current entries: `psql "$DATABASE_URL" -c 'COPY "GlossaryEntry" TO STDOUT WITH CSV HEADER' > glossary_backup.csv`.
   - Re-import when ready: `psql "$DATABASE_URL" -c "\copy \"GlossaryEntry\" FROM 'glossary_backup.csv' WITH CSV HEADER"`.
   - Rerun `make db.seed` to restore deterministic reviewer accounts.

Document deviations (e.g., temporary reviewer overrides) in the incident or release notes and update `docs/glossary-spec.md` if the workflow changes.

---

## Evaluate Retrieval

1. Ensure gold Q/A sets exist under `eval/goldset/*.jsonl`.
2. Run evaluation:

   ```bash
   make eval
   ```

   Results are written to `eval/runs/<timestamp>/metrics.json` and mirrored under `reports/` for CI artifacts.

3. Compare against baseline metrics. CI will fail if regression exceeds `EVAL_REGRESSION_THRESHOLD`.

Use the [Evaluation Metrics Interpretation](#evaluation-metrics-interpretation) section below to understand the metrics.

---

## Quality Gates & CI parity

Run `make quality` before every pull request. The target chains:

- `ruff check` / `ruff format --check`
- `mypy` across `atticus`, `api`, `ingest`, `retriever`, `eval`
- `pytest` with coverage ≥90%
- `npm run test:unit` (Vitest RBAC/unit coverage) and `npm run test:e2e` (Playwright admin/RBAC flows)
- `npm run lint`, `npm run typecheck`, `npm run build`
- Audit scripts: `npm run audit:ts`, `npm run audit:icons` (lucide import hygiene), `npm run audit:routes`, `npm run audit:py`

CI mirrors this via the `frontend-quality`, `lint-test`, and `pgvector-check` workflows. Audit reports are uploaded as artifacts under `reports/ci/` for inspection.

Formatting helpers:

```bash
npm run format      # Prettier (with tailwind sorting)
make format         # Ruff auto-fix
```

```powershell
npm run format
make format
```

---

## API & UI Operations

- Start the FastAPI service (JSON APIs only):

  ```bash
  make api
  ```

  Available at `http://localhost:8000`; FastAPI docs remain disabled in production and staging.

- Launch the Next.js workspace separately for the UI:

  ```bash
  make web-dev
  ```

  The UI expects the API to be reachable at `RAG_SERVICE_URL` (defaults to `http://localhost:8000`).
- To run a full smoke test (ingest → eval → API/UI check):

  ```bash
  make e2e
  ```

---

## Admin Ops Console

- URL: `https://<host>/admin`
- Roles:
  - **Admin** — full access to Uncertain, Tickets, and Glossary tabs. Can capture follow-up prompts, approve or escalate chats, and edit glossary entries.
  - **Reviewer** — may approve chats but cannot escalate or edit glossary entries. Glossary UI is read-only and shows a banner reflecting restricted access.
  - **User** — redirected to `/` and receives `403` responses from admin APIs.
- Data sources:
  - `Chat` records capture low-confidence conversations with `status` (`pending_review`, `reviewed`, `escalated`), `topSources[]`, and `auditLog[]` entries that chronicle actions.
  - `Ticket` records store AE escalations with `key`, `status`, `assignee`, `summary`, `lastActivity`, and `auditLog[]` metadata.
  - `RagEvent` rows track glossary and chat actions (`chat.captured`, `chat.followup_recorded`, `chat.approved`, `chat.escalated`, `glossary.*`) for audit review.
- API endpoints:
  - `GET /api/admin/uncertain` — reviewer/admin list of `pending_review` chats.
  - `POST /api/admin/uncertain/:id/approve` — reviewer/admin action to mark a chat as reviewed and stamp reviewer metadata.
  - `POST /api/admin/uncertain/:id/escalate` — admin-only action that creates a ticket, marks the chat as `escalated`, and appends audit log entries.
  - `POST /api/admin/uncertain/:id/ask-followup` — reviewer/admin action that stores a canonical follow-up prompt on the chat and extends its audit trail.
- Seed data:
  - `make db.seed` provisions a `chat-low-confidence-toner` pending review example and an `AE-1001` escalation for smoke testing.
- Rollback:
  1. `prisma migrate resolve --rolled-back "20251018090000_admin_ops_console"` (marks the migration reversed).
  2. Drop `Chat` and `Ticket` tables (or restore from backup) if the migration was applied.
  3. Remove the admin console routes/components and revert `prisma/seed.ts` to clear sample data.
  4. Re-run `npm run build` and `PYTHONPATH=. pytest tests/unit/admin-uncertain-route.test.ts -q` to confirm restoration.

---

## Escalation Email (SES)

- Requires valid SES **SMTP credentials** (not IAM keys).
- Ensure the `CONTACT_EMAIL` and all `SMTP_*` environment variables are correctly set in `.env`.
- Maintain `SMTP_ALLOW_LIST` so only vetted recipients/senders receive escalations; mismatches raise actionable errors.
- The SES identity for `SMTP_FROM` must be verified; sandbox mode also requires verified recipients.
- For security, lock down SES with an IAM policy restricting `ses:FromAddress` to approved senders and region (see [SECURITY.md](SECURITY.md)).
- Escalation emails append structured trace payloads (user/chat/message IDs, top documents) and include the `trace_id` for log correlation.

---

## Snapshot & Rollback

1. Snapshot the `indices/` directory during each release.
2. To revert to a previous snapshot:

   ```bash
   python scripts/rollback.py --manifest indices/manifest.json
   ```

3. After rollback, run a smoke evaluation:

   ```bash
   make eval
   ```

   and test a few known gold queries with `/ask`.

---

## Observability & Debugging

- **Logs**
  - Info: `logs/app.jsonl`
  - Errors: `logs/errors.jsonl`
- **Sessions view**
  - `GET /admin/sessions?format=html|json`
- **Metrics dashboard**
  - `GET /admin/metrics` exposes query/escalation counters, latency histograms, and rate-limit stats.
- **Rate limiting**
  - Defaults to `RATE_LIMIT_REQUESTS=5` per `RATE_LIMIT_WINDOW_SECONDS=60`; violations emit hashed identifiers in `logs/app.jsonl`.
- **Verbose tracing**
  - Set `LOG_VERBOSE=1` and `LOG_TRACE=1` in `.env` and restart the service.
- **Environment diagnostics**
  - `python scripts/debug_env.py` shows the source and fingerprint of every secret.

---

## Dependency risk exceptions

`npm audit` (2025-09-28) flags one critical and seven moderate/low vulnerabilities tied to the current Next.js (14.2.5), @auth/core, esbuild, vite, and vitest toolchain. Upstream patches are pending; monitor Next.js security advisories (GHSA-f82v-jwr5-mffw, GHSA-gp8f-8m3g-qvj9) and plan an upgrade when 14.2.7+ ships with fixes. Track the audit output locally via:

```bash
npm audit --json > reports/ci/npm-audit-latest.json
```

Document mitigation status in security reviews and ensure `frontend-quality` continues to surface `reports/ci/*.json` artifacts for traceability.

---

## Evaluation Metrics Interpretation

When you run `make eval`, metrics appear in `eval/runs/<timestamp>/metrics.json`.
They measure how well retrieval surfaces the right evidence for answer generation.

### Core Metrics

| Metric          | What it Measures                                                 | Ideal Range        | Notes                                   |
| --------------- | ---------------------------------------------------------------- | ------------------ | --------------------------------------- |
| **nDCG@K**      | Quality of ranking — are the best chunks at the top?             | 0.85–1.0 excellent | Higher is better; discounts lower ranks |
| **Recall@K**    | Percentage of questions with at least one correct chunk in top-K | >=0.9 excellent    | Indicates coverage                      |
| **MRR@K**       | How early the first correct chunk appears                        | >=0.7 excellent    | Rewards early hits                      |
| **Precision@K** | Fraction of retrieved chunks that are relevant                   | Context dependent  | Useful when keeping context small       |

### Secondary Metrics

- **HitRate@K**: simpler recall variant — was _any_ relevant item retrieved?
- **MAP** (Mean Average Precision): averages precision across ranks.
- **Coverage**: fraction of gold questions for which any relevant doc exists in the corpus.
- **Latency**: median and 95th percentile retrieval time.

### Typical Thresholds for CI

Fail the evaluation if:

- `nDCG@10` drops more than **3–5%** compared to baseline.
- `Recall@10` drops more than **5%**.
- `MRR@10` drops more than **5–10%**.

These can be tuned for production needs (e.g., stricter for tenders).

### Diagnosing Drops

- **Recall drops, nDCG stable** → content drift or chunk sizes need adjustment.
- **nDCG drops, Recall stable** → ranking issue; consider enabling a reranker.
- **Both drop** → ingestion or index regression.
- **Precision drops, Recall stable** → too many loosely relevant chunks; adjust `MAX_CONTEXT_CHUNKS` or hybrid thresholds.

Example metrics block:

```json
{
  "metrics": {
    "ndcg@10": 0.86,
    "recall@10": 0.92,
    "mrr@10": 0.74,
    "precision@5": 0.62,
    "latency_ms_p50": 62,
    "latency_ms_p95": 110
  },
  "dataset": "eval/goldset/sales_faq.jsonl",
  "index_fingerprint": "3d7c1b...f12",
  "model": {
    "embed": "text-embedding-3-large@2025-01-15",
    "gen": "gpt-4.1"
  }
}
```

Interpretation: strong ranking and recall, with fast median latency.

---

## References

- [README.md](README.md) — first-time setup and Make targets
- [AGENTS.md](AGENTS.md) — architecture and error policy
- [SECURITY.md](SECURITY.md) — secrets and IAM policy
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — quick fixes

<!-- End file: OPERATIONS.md -->

## README.md

<!-- Begin file: README.md -->

# Atticus

> **Atticus for Sales Enablement** accelerates tender responses, keeps Sales self-sufficient, and frees Service/Marketing from ad-hoc requests.

Atticus is a Retrieval-Augmented Generation (RAG) assistant built on **Next.js**, **FastAPI**, **Postgres + pgvector**, **Prisma**, and **Auth.js**. It ingests content, indexes it with pgvector, and serves grounded answers with citations. When confidence is low the system sends a cautious partial answer and escalates via email.

> **Release 0.7.10** – Locked the Next.js workspace in as the only UI, aligned API metadata with the central `VERSION` file, and refreshed operations docs for the split frontend/backend stack.

## Model Disambiguation Flows

- **Direct hit** — when a question names a specific model (for example, "Apeos C4570"), retrieval is scoped to that family and a single answer with family-tagged sources is returned.
- **Unclear** — if no confident match is found, `/api/ask` returns a `clarification` payload with the available families. The chat UI renders the clarification card and resubmits the prior question with an explicit `models` array when the user picks an option.
- **Multi-model** — if several models are detected or supplied, Atticus fans out retrieval per model and responds with `answers[]`, keeping citations separate for each model while still providing the aggregated `sources` list for backwards compatibility.
- **Testing** — `tests/test_model_parser.py`, `tests/test_retrieval_filters.py`, `tests/test_chat_route.py`, `tests/test_ui_route.py`, and `tests/playwright/chat.spec.ts` lock these behaviours in place.

---

## Quick Start

1. Bootstrap environment variables

    Generate a local `.env` so secrets stay inside the repository:

    ```bash
    python scripts/generate_env.py
    python scripts/debug_env.py  # inspect precedence when overriding values
    ```

    Populate SMTP settings for escalation email delivery:

    - `CONTACT_EMAIL` – escalation recipient
    - `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM` – SES SMTP credentials
    - `SMTP_ALLOW_LIST` – comma-separated sender/recipient allow list
    - `RAG_SERVICE_URL` – FastAPI retrieval service (defaults to `http://localhost:8000`)

1. Install dependencies

    Install Python tooling (Ruff, mypy, pytest, etc.) and Node packages (Next.js workspace, shadcn/ui, Knip).

    ```powershell
    pip install -U pip pip-tools
    pip-compile -U requirements.in
    pip-sync requirements.txt
    npm install
    ```

1. Database and Prisma

    Launch Postgres, apply migrations, and seed the default admin specified in `.env`.

    ```bash
    make db.up
    make db.migrate   # runs `prisma generate` before applying migrations
    # POSIX shells (bash/zsh): export DATABASE_URL before verification
    set -a
    . .env
    set +a
    make db.verify    # pgvector extension, dimension, IVFFlat probes
    make db.seed
    ```

    > Windows users: do **not** run the `set -a` snippet—instead use the PowerShell block below (or rely on `make db.verify`, which now auto-loads `.env` values automatically).

    ```powershell
    make db.up
    make db.migrate
    Get-Content .env | ForEach-Object {
    if ($_ -and $_ -notmatch '^#') {
        $name, $value = $_.Split('=', 2)
        if ($value) { [System.Environment]::SetEnvironmentVariable($name.Trim(), $value.Trim(), 'Process') }
    }
    }
    make db.verify
    make db.seed
    ```

    `make db.verify` auto-loads `.env`, then shells out to `psql` (falling back to `docker compose exec postgres psql` when the CLI is unavailable) and will emit a notice if your pgvector build caps ANN indexes at 2K dimensions; upgrade the image to regain IVFFlat on 3K-dim embeddings.

    Run the verification SQL directly when debugging:

    ```bash
    psql "$DATABASE_URL" \
      -v expected_pgvector_dimension=${PGVECTOR_DIMENSION:-3072} \
      -v expected_pgvector_lists=${PGVECTOR_LISTS:-100} \
      -f scripts/verify_pgvector.sql
    ```

    ```powershell
    if (-not $env:PGVECTOR_DIMENSION) { $env:PGVECTOR_DIMENSION = 3072 }
    if (-not $env:PGVECTOR_LISTS) { $env:PGVECTOR_LISTS = 100 }
    psql "$env:DATABASE_URL" `
    -v expected_pgvector_dimension=$env:PGVECTOR_DIMENSION `
    -v expected_pgvector_lists=$env:PGVECTOR_LISTS `
    -f scripts/verify_pgvector.sql
    ```

1. Ingest documents

    Run ingestion once after the database is ready so the assistant has content to answer with; rerun whenever new documents land. `make eval` and `make seed` help during iteration.

    ```bash
    make ingest     # parse, chunk, embed, and update pgvector index
    make seed       # generate deterministic seed manifest (seeds/seed_manifest.json)
    make eval       # run retrieval evaluation and emit metrics under eval/runs/
    ```

    > **Note:** The CED chunker now operates with zero token overlap by default
    > (`CHUNK_OVERLAP_TOKENS=0`). Override the environment variable if a
    > different stride is required for specialised corpora.

1. Run services

    Use separate terminals for the FastAPI backend and the Next.js UI.

    ```bash
    make api        # FastAPI service on http://localhost:8000
    make web-dev    # Next.js workspace on http://localhost:3000
    ```

    ```powershell
    make api
    make web-dev
    ```

1. Quality gates (before committing)

    ```bash
    make quality
    ```

    ```powershell
    make quality
    ```

    `make quality` mirrors CI by running Ruff, mypy, pytest (>=90% coverage), Vitest unit tests, Next.js lint/typecheck/build, Playwright RBAC coverage, version parity checks, and all audit scripts (Knip, icon usage, route inventory, Python dead-code audit). Pre-commit hooks now include Ruff, mypy, ESLint (Next + tailwindcss), Prettier (with tailwind sorting), and markdownlint. Install with `pre-commit install`.

1. Authenticate with magic link

    Visit `http://localhost:3000/signin`, request a magic link for your provisioned email, and follow the link (from your inbox or `AUTH_DEBUG_MAILBOX_DIR`, which defaults to `./logs/mailbox`) to sign in. Admins and reviewers can reach `/admin` to triage low-confidence chats, capture follow-up prompts, review escalations, and curate glossary entries (reviewers operate in read-only mode for glossary changes).

1. `/api/ask` contract

    The Next.js app exposes `/api/ask`, proxying the FastAPI retrieval service through server-sent events (SSE).
    FastAPI still returns canonical JSON; the proxy synthesises `start`, `answer`, and `end` events so the UI can subscribe using a single streaming interface.

    **Request**

    ```json
    {
    "question": "What is the pilot timeline?",
    "contextHints": ["Managed print"],
    "topK": 8
    }
    ```

    **Response**

    ```json
    {
    "answer": "...",
    "sources": [{ "path": "content/pilot.pdf", "page": 3 }],
    "confidence": 0.82,
    "request_id": "abc123",
    "should_escalate": false
    }
    ```

    Send `Accept: text/event-stream` to receive incremental events; `lib/ask-client.ts` handles SSE parsing, JSON fallback, and request-id logging.

    ---

## Developer workflow

1. **Environment**:
   - Generate `.env` and update SMTP + Postgres credentials. 
   - Ensure `AUTH_SECRET` and `NEXTAUTH_SECRET` match.
   - Set `NEXTAUTH_URL` (typically `http://localhost:3000` for local dev).
2. **Dependencies**:
   - install Python + Node dependencies (`pip-sync` and `npm install`).
3. **Database**:
   - Run `make db.up && make db.migrate && make db.seed`. 
   - Export `.env` before `make db.verify` so `DATABASE_URL` is available (`set -a; . .env; set +a` on POSIX shells, or use the PowerShell snippet in Quick Start on Windows).
4. **Quality**: 
   - Run `make quality` locally before every PR. 
   - Fix formatting with `npm run format` (Prettier) and `make format` (Ruff) as needed.
5. **Run** 
   - `make api`
   - `make web-dev` for local development.
6. **Observe**
   - `logs/app.jsonl`
   - `logs/errors.jsonl`
   - `/admin/metrics` (dashboard)
7. **Release**
   - Follow [RELEASE.md](RELEASE.md) for tagging.
   - Upgrade/rollback steps, confirming `VERSION` matches `package.json` before tagging.

8. **Git**
   - Git pre-commit hooks enforce Ruff, mypy, ESLint, Prettier, markdownlint, and repository hygiene
    - Use `pre-commit run --all-files` to verify manually.

---

## Frontend design system

- Shared primitives built on shadcn/ui live under [`components/ui`](components/ui). Compose new surfaces with these building blocks instead of bespoke Tailwind markup to keep typography, spacing, and focus states consistent.
- Cards (`Card`, `CardHeader`, `CardContent`, etc.) wrap dashboard panels, admin glossaries, and contact forms with rounded borders and responsive padding.
- Badges (`Badge`) expose semantic variants (`default`, `success`, `warning`, `destructive`, etc.) for status chips, streaming indicators, and keyboard shortcut callouts.
- Buttons now support the `asChild` pattern for wrapping Next.js `Link` components, ensuring consistent styling for navigation pills and in-form actions.

---

## CI and quality gates

GitHub Actions enforces:

- **frontend-quality** – Node 20 + Postgres service, running `npm run lint`, `npm run typecheck`, `npm run build`, and all audit scripts (`npm run audit:ts`, `npm run audit:icons`, `npm run audit:routes`, `npm run audit:py`). Audit outputs are uploaded as artifacts under `frontend-audit-reports`.
- **lint-test** – Python 3.12 toolchain running Ruff (lint + format check), mypy, pytest with ≥90% coverage, and pre-commit.
- **pgvector-check** – Applies Prisma migrations against pgvector-enabled Postgres and runs `make db.verify`.
- **eval-gate** – Retrieval evaluation regression checks (see [eval-gate.yml](.github/workflows/eval-gate.yml)).

Always confirm local `make quality` mirrors CI before pushing.

---

## Make targets

| Target                      | Description                                                         |
| --------------------------- | ------------------------------------------------------------------- |
| `make env`                  | Generate `.env` from defaults                                       |
| `make ingest`               | Parse, chunk, embed, and update the pgvector index                  |
| `make seed`                 | Generate deduplicated seed manifest (`seeds/seed_manifest.json`)    |
| `make eval`                 | Run retrieval evaluation and write metrics under `eval/runs/`       |
| `make api`                  | Start FastAPI backend                                               |
| `make web-dev`              | Run Next.js dev server (port 3000)                                  |
| `make app-dev`              | Alias for `make web-dev`                                            |
| `make db.up`                | Start Postgres (Docker)                                             |
| `make db.down`              | Stop Postgres (Docker)                                              |
| `make db.migrate`           | Run Prisma migrations                                               |
| `make db.verify`            | Ensure pgvector extension, dimensions, and IVFFlat settings         |
| `make db.seed`              | Seed default organization/admin                                     |
| `make help`                 | List available make targets                                         |
| `make web-build`            | Build the production Next.js bundle                                 |
| `make web-start`            | Start the built Next.js app                                         |
| `make web-lint`             | Run Next.js lint checks                                             |
| `make web-typecheck`        | Type-check the UI with TypeScript                                   |
| `make web-test`             | Run Vitest unit tests                                               |
| `make web-e2e`              | Run Playwright smoke tests                                          |
| `make smtp-test`            | Send an SES test email                                              |
| `make smoke`                | Run FastAPI health probe                                            |
| `make test.unit`            | Unit tests for hashing, config reload, mailer, chunker, seeds, eval |
| `make test.api`             | API contract tests (ask/contact/error schema/UI)                    |
| `make test`                 | Run pytest suite with coverage >=90%                                |
| `make lint` / `make format` | Ruff lint + auto-fix                                                |
| `make typecheck`            | Run mypy over atticus/api/ingest/retriever/eval                     |
| `make quality`              | Combined Python + Next quality gates, version-parity check, and audits |
| `make web-audit`            | Run Node and Python audit scripts                                   |

---

## Observability & guardrails

- Every request receives a `request_id` propagated through logs, metrics, and escalation emails.
- Rate limiting enforces `RATE_LIMIT_REQUESTS` per `RATE_LIMIT_WINDOW_SECONDS`; extra calls return a structured `429 rate_limited` payload.
- Metrics (queries, escalations, latency) persist via `atticus.metrics.MetricsRecorder` and surface on `/admin/metrics` and CSV exports under `reports/`.
- Evaluation artifacts live under `eval/runs/<timestamp>/` and `reports/` for CI comparisons.

---

## Web UI

The Next.js application in `app/` is the supported interface.

- `app/page.tsx` hosts the streaming chat surface using `/api/ask` and renders citations.
- `app/contact/page.tsx` handles escalations to the FastAPI `/contact` endpoint.
- `app/admin/page.tsx` powers the glossary workflow and enforces Auth.js RBAC.

Legacy static assets live under `archive/legacy-ui/` for reference only.

---

## Auth & RBAC

- Email magic links deliver sign-in using SES SMTP credentials from `.env`.
- Admins (`ADMIN_EMAIL`) manage the Uncertain, Tickets, and Glossary tabs at `/admin`. Reviewers share the same surface with approval capabilities but cannot escalate chats or edit glossary entries. Standard users are redirected to `/`.
- Postgres Row Level Security gates glossary CRUD, user/session tables, and admin APIs by `org_id` + role.
- Use `withRlsContext(session, fn)` for Prisma calls that inherit user context.

Provisioning and rollback procedures are documented in [docs/runbooks/auth-rbac.md](docs/runbooks/auth-rbac.md).

---

## Documentation map

- [AGENTS.md](AGENTS.md) – architecture, environment settings, audit/CI requirements
- [ARCHITECTURE.md](ARCHITECTURE.md) – system diagram, data flow, SSE contract
- [OPERATIONS.md](OPERATIONS.md) – runbooks, metrics, and incident response
- [RELEASE.md](RELEASE.md) – release process, upgrade/rollback steps
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) – common setup, Auth.js, pgvector, SSE issues
- [REQUIREMENTS.md](REQUIREMENTS.md) – functional/non-functional requirements for the Next.js + pgvector stack
- [AUDIT_REPORT.md](AUDIT_REPORT.md) / [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) – remediation history
- [CHANGELOG.md](CHANGELOG.md) – release history
- [CONTRIBUTING.md](CONTRIBUTING.md) – contributor workflow
- [STYLEGUIDE.md](STYLEGUIDE.md) – code and writing standards
- [TODO.md](TODO.md) / [TODO_COMPLETE.md](TODO_COMPLETE.md) – authoritative backlog

---

## License

See [LICENSE](LICENSE).

<!-- End file: README.md -->

## RELEASE.md

<!-- Begin file: RELEASE.md -->

# RELEASE — Atticus

This document describes the official release process for Atticus.
Follow these steps to ensure every release is versioned, tested, and documented correctly.

---

## Versioning

Atticus uses **Semantic Versioning**: `MAJOR.MINOR.PATCH`.

- **MAJOR** — Incompatible API changes or breaking architecture changes.
- **MINOR** — Backwards-compatible feature additions or improvements.
- **PATCH** — Backwards-compatible bug fixes or documentation updates.

---

## Release Checklist

1. **Update CHANGELOG**
   - Edit [CHANGELOG.md](CHANGELOG.md) with the new version number, date, and highlights.
2. **Verify Environment**
   - Confirm `.env` is complete and correct using:

     ```bash
     python scripts/debug_env.py
     ```

3. **Run Full Quality Gates**
   - Ensure the following commands pass locally:

     ```bash
     make quality         # Ruff + mypy + pytest + Next lint/typecheck/build + audits
     npm run format:check # Prettier enforcement
     pre-commit run --all-files --show-diff-on-failure
     make eval            # Retrieval regression suite
     make e2e             # Optional but recommended before tagging
     ```

   - CI requires ≥90% coverage and enforces evaluation regression thresholds.

4. **Sync Versioning**
   - Update [`VERSION`](VERSION), `package.json`, and [CHANGELOG.md](CHANGELOG.md) with the new semantic version (e.g. `0.7.0`).
   - Confirm the values match by running `node -p "require('./package.json').version"` and comparing with `cat VERSION`.
   - Commit the changes with a descriptive message (e.g. `release(0.7.0): developer experience + docs sync`).
5. **Tag the Release**
   - Tag using semantic versioning, e.g. `v0.7.0`:

     ```bash
     git tag v0.7.0
     git push origin v0.7.0
     ```

   - Pushing the tag triggers the `release.yml` GitHub Action.

---

## Post‑Release

- Monitor `logs/app.jsonl` and `logs/errors.jsonl` for early issues.
- Announce the release internally and update any dependent services or documentation.
- Archive `reports/ci/*.json` and evaluation dashboards for audit trails.

---

## Upgrade / Rollback Playbook

### Upgrade

1. Pull the tagged release (`git fetch --tags && git checkout vX.Y.Z`).
2. Run database migrations and seed updates:

   ```bash
   make db.migrate
   make db.seed
   ```

3. Rebuild the Next.js app and restart services:

   ```bash
   npm install --production
   npm run build
   docker compose up -d --build
   ```

  > **Note:** Release 0.7.11 adds Prisma `Chat`/`Ticket` tables plus the tabbed admin console and RBAC APIs. Run `make db.migrate && make db.seed` before `npm run build` so low-confidence chat data and escalations materialise in the UI.
  > **Note:** Release 0.8.0 enforces the `app.pgvector_lists` GUC, introduces the `RagEvent` audit ledger, and adds glossary upsert/follow-up workflows. Run `make db.migrate`, `make db.verify`, and `npm run db:seed` before `npm run build`, and wire `make version-check` into CI to detect version drift early.

4. Verify health:

   ```bash
   make smoke
   make eval
   ```

5. Review audit artifacts (`reports/ci/`, `eval/runs/`) to confirm no regressions.

### Rollback

1. Checkout the previous tag and redeploy (`git checkout vX.Y.(Z-1)` followed by the upgrade steps above).
2. Restore index snapshots using `python scripts/rollback.py --manifest indices/manifest.json` if ingestion changes shipped.
3. Re-run `make eval` and `make quality` to ensure the rolled-back version is healthy.
4. Update status pages/runbooks with the rollback rationale and next steps.

---

## References

- [CHANGELOG.md](CHANGELOG.md) — full version history.
- [OPERATIONS.md](OPERATIONS.md) — runbooks and evaluation metrics.
- [SECURITY.md](SECURITY.md) — secrets management and IAM policy examples.

<!-- End file: RELEASE.md -->

## REPO_STRUCTURE.md

<!-- Begin file: REPO_STRUCTURE.md -->

# Repository Structure Snapshot

Key directories to understand when working on Atticus.

- `app/`
  - `page.tsx` – streaming chat surface using the unified `/api/ask` contract.
  - `admin/` – admin console surfacing Uncertain, Tickets, and Glossary tabs for reviewers/admins.
  - `contact/` – escalation form backed by the FastAPI `/contact` endpoint.
  - `signin/`, `settings/`, `apps/` – additional Next.js routes.
- `components/`
  - `chat/` – chat panel client components.
  - `admin/` – console widgets (tabs, tables) powering `/admin`.
  - `glossary/` – admin glossary UI using shadcn-style primitives.
  - `ui/` – shared button/input/table components.
- `lib/`
  - `ask-client.ts`, `ask-contract.ts` – shared DTOs and streaming helpers.
  - `auth.ts`, `rls.ts`, `utils.ts` – auth, row-level security, and UI helpers.
- `api/`
  - `main.py` – FastAPI entry point wiring dependencies/middleware.
  - `routes/` – JSON APIs (`chat.py`, `contact.py`, `ingest.py`, etc.); no templates or static mounts remain in FastAPI.
  - `middleware.py`, `schemas.py` – shared FastAPI utilities and contracts.
- `atticus/`, `retriever/`, `ingest/`, `eval/` – Python services and pipelines for ingestion, retrieval, and evaluation.
- `prisma/` – Prisma schema and migrations for auth, glossary, chat review, and ticket data.
- `scripts/` – operational tooling (env generation, audits, ingestion, eval, etc.).
- `tests/`
  - Python pytest suites covering API contracts, ingestion utilities, and auth flows.
- `archive/legacy-ui/` – historical static HTML prototype retained for reference only.
- `content/`, `indices/`, `reports/`, `logs/` – document corpus, vector indices, evaluation artifacts, and log outputs.

Supporting docs live at the repository root (`README.md`, `AGENTS.md`, `ARCHITECTURE.md`, `OPERATIONS.md`, etc.).

<!-- End file: REPO_STRUCTURE.md -->

## REPO_TREE.md

<!-- Begin file: REPO_TREE.md -->

# Repository Tree

Generated: 2025-10-09 07:22:24 UTC
Root: `C:\Dev\Atticus`
Directories: 64
Files: 223

- `/`
  - `.github/`
    - `workflows/`
      - `auto-fix-ruff.yml`
      - `eval-gate.yml`
      - `lint-test.yml`
      - `release.yml`
  - `.vscode/`
    - `extensions.json`
  - `api/`
    - `routes/`
      - `__init__.py`
      - `admin.py`
      - `chat.py`
      - `contact.py`
      - `eval.py`
      - `health.py`
      - `ingest.py`
    - `Dockerfile`
    - `__init__.py`
    - `dependencies.py`
    - `errors.py`
    - `main.py`
    - `middleware.py`
    - `rate_limit.py`
    - `schemas.py`
    - `utils.py`
  - `app/`
    - `admin/`
      - `page.tsx`
    - `api/`
      - `ask/`
        - `route.ts`
      - `auth/`
        - `[...nextauth]/`
          - `route.ts`
      - `glossary/`
        - `[id]/`
          - `route.ts`
        - `route.ts`
        - `utils.ts`
    - `apps/`
      - `page.tsx`
    - `contact/`
      - `page.tsx`
    - `settings/`
      - `page.tsx`
    - `signin/`
      - `verify/`
        - `page.tsx`
      - `page.tsx`
    - `globals.css`
    - `layout.tsx`
    - `page.tsx`
    - `providers.tsx`
  - `atticus/`
    - `notify/`
      - `__init__.py`
      - `mailer.py`
    - `utils/`
      - `__init__.py`
      - `hashing.py`
    - `__init__.py`
    - `config.py`
    - `embeddings.py`
    - `logging.py`
    - `logging_utils.py`
    - `metrics.py`
    - `tokenization.py`
    - `vector_db.py`
  - `components/`
    - `auth/`
      - `sign-in-form.tsx`
    - `chat/`
      - `chat-panel.tsx`
    - `glossary/`
      - `admin-panel.tsx`
    - `ui/`
      - `button.tsx`
      - `input.tsx`
      - `label.tsx`
      - `select.tsx`
      - `table.tsx`
      - `textarea.tsx`
    - `AnswerRenderer.tsx`
    - `page-header.tsx`
    - `site-footer.tsx`
    - `site-header.tsx`
  - `content/`
    - `model/`
      - `Shobu/`
        - `Apeos C7070-C6570-C5570-C4570-C3570-C3070-C2570-CSO-FN-CED-362.pdf`
        - `ac7070_qna.xlsx`
  - `content_unused/`
    - `Reiki/`
      - `Apeos C8180 C7580 C6580 CSO-FN-CED 363.pdf`
    - `Shobu2/`
      - `Apeos C7071 C6571 C5571 C4571 CSO-FN-CED - 406.pdf`
    - `Sorai/`
      - `Advanced/`
        - `Apeos C3567 C3067 C2567 CSO-FN-CED - 407.pdf`
      - `Basic/`
        - `Apeos C3061 C2561 C2061 CSO-FN-CED - 409.pdf`
  - `docs/`
    - `api/`
      - `README.md`
      - `openapi.json`
    - `runbooks/`
      - `auth-rbac.md`
    - `ATTICUS_DETAILED_GUIDE.md`
    - `README.md`
    - `REMOTE_ACCESS.md`
    - `glossary-spec.md`
  - `eval/`
    - `harness/`
      - `__init__.py`
      - `test_eval.py`
      - `test_ui.py`
    - `runs/`
      - `20251008/`
        - `metrics.csv`
        - `metrics.html`
        - `summary.json`
      - `ci/`
        - `metrics.csv`
        - `summary.json`
      - `manual/`
        - `metrics.csv`
        - `summary.json`
      - `.gitkeep`
    - `__init__.py`
    - `baseline.json`
    - `ced-362-smoke.csv`
    - `gold_set.csv`
    - `runner.py`
  - `examples/`
    - `dev.http`
  - `indices/`
    - `.gitkeep`
  - `ingest/`
    - `parsers/`
      - `__init__.py`
      - `docx.py`
      - `html.py`
      - `image.py`
      - `pdf.py`
      - `text.py`
      - `xlsx.py`
    - `__init__.py`
    - `chunker.py`
    - `models.py`
    - `pipeline.py`
  - `lib/`
    - `ask-client.ts`
    - `ask-contract.ts`
    - `auth.ts`
    - `prisma.ts`
    - `rbac.ts`
    - `rls.ts`
    - `utils.ts`
  - `nginx/`
    - `certs/`
      - `.gitkeep`
    - `Dockerfile`
    - `nginx.conf`
  - `prisma/`
    - `migrations/`
      - `20240702120000_auth_rbac/`
        - `migration.sql`
      - `20240708123000_pgvector_schema/`
        - `migration.sql`
      - `20240709150000_glossary_review_workflow/`
        - `migration.sql`
      - `20250201090000_fix_updated_at_trigger/`
        - `migration.sql`
      - `20251008090000_pgvector_bootstrap/`
        - `migration.sql`
    - `schema.prisma`
    - `seed.ts`
  - `retriever/`
    - `__init__.py`
    - `answer_format.py`
    - `citation_utils.py`
    - `generator.py`
    - `models.py`
    - `service.py`
    - `vector_store.py`
  - `scripts/`
    - `.gitkeep`
    - `atticus_cli.py`
    - `audit_unused.py`
    - `check_version_parity.py`
    - `chunk_ced.py`
    - `db_verify.py`
    - `debug_env.py`
    - `e2e_smoke.py`
    - `eval_qa.py`
    - `eval_run.py`
    - `generate_api_docs.py`
    - `generate_env.py`
    - `icon-audit.mjs`
    - `ingest_cli.py`
    - `list_make_targets.py`
    - `make_seed.py`
    - `rollback.md`
    - `rollback.py`
    - `route-audit.mjs`
    - `run_ingestion.py`
    - `smtp_test.py`
    - `test_health.py`
    - `verify_pgvector.sql`
  - `seeds/`
    - `README.md`
    - `seed_manifest.json`
  - `tests/`
    - `playwright/`
      - `rbac.spec.ts`
    - `unit/`
      - `ask-client.test.ts`
      - `rbac.test.ts`
    - `test_admin_route.py`
    - `test_chat_route.py`
    - `test_chunker.py`
    - `test_citation_dedupe.py`
    - `test_config_reload.py`
    - `test_contact_route.py`
    - `test_environment_diagnostics.py`
    - `test_error_schema.py`
    - `test_eval_runner.py`
    - `test_hashing.py`
    - `test_ingestion_retrieval_integration.py`
    - `test_mailer.py`
    - `test_seed_manifest.py`
    - `test_ui_route.py`
  - `.codex-touch`
  - `.editorconfig`
  - `.env.example`
  - `.eslintrc.json`
  - `.gitattributes`
  - `.gitignore`
  - `.markdownlint-cli2.yaml`
  - `.pre-commit-config.yaml`
  - `.prettierignore`
  - `.prettierrc.json`
  - `AGENTS.md`
  - `ALL_CODE.md`
  - `ALL_DOCS.md`
  - `ARCHITECTURE.md`
  - `Atticus.code-workspace`
  - `CHANGELOG.md`
  - `COMPILED_DOCS.md`
  - `COMPILED_SCRIPTS.md`
  - `CONTRIBUTING.md`
  - `IMPLEMENTATION_PLAN.md`
  - `LICENSE`
  - `Makefile`
  - `OPERATIONS.md`
  - `README.md`
  - `RELEASE.md`
  - `REPO_STRUCTURE.md`
  - `REPO_TREE.md`
  - `REQUIREMENTS.md`
  - `SECURITY.md`
  - `STYLEGUIDE.md`
  - `TODO.md`
  - `TODO_COMPLETE.md`
  - `TROUBLESHOOTING.md`
  - `VERSION`
  - `code.md`
  - `codex_instructions.md`
  - `combine-code.ps1`
  - `config.yaml`
  - `docker-compose.yml`
  - `knip.json`
  - `middleware.ts`
  - `next-auth.d.ts`
  - `next-env.d.ts`
  - `next.config.js`
  - `package-lock.json`
  - `package.json`
  - `playwright.config.ts`
  - `postcss.config.js`
  - `pyproject.toml`
  - `requirements.in`
  - `requirements.txt`
  - `tailwind.config.js`
  - `tsconfig.json`
  - `vitest.config.ts`

<!-- End file: REPO_TREE.md -->

## REQUIREMENTS.md

<!-- Begin file: REQUIREMENTS.md -->

# REQUIREMENTS — Atticus

This document defines the runtime and build requirements for Atticus.
Use it to set up development environments, run CI, and deploy production services.

---

## Core Runtime

- **Python 3.12** — Required for both development and production.
- **Node.js 20 LTS** — Required for the Next.js workspace, lint/typecheck/build, and audit scripts.
- **Operating System** — Linux or Windows. Windows users should ensure Tesseract and Ghostscript are installed if PDF OCR is needed.

---

## Python Dependencies

Dependencies are managed with `pip-tools` for deterministic builds.

- `requirements.in` — human-maintained top‑level packages.
- `requirements.txt` — fully pinned output generated by:
  ```bash
  pip-compile -U requirements.in
  ```
- Synchronize the environment with:
  ```bash
  pip-sync requirements.txt
  ```

Typical core packages include:

- `fastapi`, `uvicorn`
- `pydantic`, `python-dotenv`
- `pgvector`, `psycopg`, `numpy`, `scikit-learn`, `rapidfuzz`
- `pymupdf`, `pdfminer.six`, `pytesseract`, `Pillow`
- `pytest`, `pytest-cov`

These are already captured and pinned in `requirements.in` and `requirements.txt`.

---

## Node & Frontend Dependencies

Managed via `package.json` / `package-lock.json` with `npm install`.

Key packages:

- `next@14.2.5`, `react@18`, `react-dom@18`
- `next-auth@4` with `@auth/prisma-adapter`
- `tailwindcss@3`, `shadcn/ui` components, `lucide-react`
- `typescript@5.4`, `eslint@8.57`, `eslint-config-next`, `eslint-plugin-tailwindcss`
- `prettier@3.3` + `prettier-plugin-tailwindcss`
- Tooling: `knip`, `vitest`, `@playwright/test`

Install once with `npm install` (POSIX/PowerShell). Use `npm ci` inside CI.

---

## Environment Variables

All runtime configuration is supplied through `.env` (generated by `scripts/generate_env.py`).
Key variables include:

| Variable                                           | Purpose                                                    |
| -------------------------------------------------- | ---------------------------------------------------------- |
| `OPENAI_API_KEY`                                   | Access key for GPT and embeddings                          |
| `GEN_MODEL`                                        | Generation model (default `gpt-4.1`)                       |
| `EMBED_MODEL`                                      | Embedding model (default `text-embedding-3-large`)         |
| `DATABASE_URL`                                     | Postgres connection string for pgvector                    |
| `NEXTAUTH_SECRET`, `NEXTAUTH_URL`                  | Auth.js session signing and callback origin                |
| `EMAIL_SERVER`, `EMAIL_FROM`                       | Auth.js email provider configuration                       |
| `CONTACT_EMAIL`, `SMTP_*`, `SMTP_ALLOW_LIST`       | Escalation email settings and allow-list guardrail         |
| `AUTH_DEBUG_MAILBOX_DIR`                           | Local directory where magic-link emails are written in dev. Defaults to `./logs/mailbox`. |
| `RAG_SERVICE_URL`                                  | Base URL for FastAPI retrieval service proxied by Next.js  |
| `ENABLE_RERANKER`                                  | Toggle hybrid reranking (defaults to disabled)             |
| `SMTP_DRY_RUN`                                     | Log escalation attempts without sending email              |
| `RATE_LIMIT_REQUESTS`, `RATE_LIMIT_WINDOW_SECONDS` | Per-user/IP rate limit configuration                       |
| `LOG_VERBOSE`, `LOG_TRACE`                         | Enable structured trace logging                            |

Run `python scripts/debug_env.py` to verify that environment settings are sourced and fingerprinted correctly.

---

## Development Tooling

- **Ruff** for linting and import sorting (`make lint`, `make format`).
- **mypy** for static type checking (`make typecheck`).
- **pytest** for testing (`make test`), with a target of ≥90% coverage.
- **ESLint** (`npm run lint`) with the Tailwind plugin for shadcn/ui class validation.
- **Prettier** (`npm run format`, `npm run format:check`) with tailwindcss plugin enforcing class order.
- **TypeScript compiler** (`npm run typecheck`) and **Next.js build** (`npm run build`).
- **Vitest / Playwright** for unit and smoke testing (`npm run test:unit`, `npm run test:e2e`).
- Optional: `pytest-xdist` for parallel test runs; if installed, Makefile will automatically add `-n auto`.
- **pre-commit** hooks covering Ruff, mypy, ESLint, Prettier, markdownlint (`pre-commit install`).

---

## CI Expectations

Local workflows must mirror CI:

- Run `make quality` before pushing.
- Ensure audit artifacts under `reports/ci/` remain ignored locally (`.gitignore` handles this).
- GitHub Actions jobs `frontend-quality`, `lint-test`, and `pgvector-check` enforce the same commands with Node 20 + Python 3.12 matrices.

---

## Deployment

- Use Docker Compose for reproducible production deployments.
- Ensure `.env` is present and up to date before running:
  ```bash
  docker compose up --build
  ```
- The default configuration exposes the API at `http://localhost:8000` with TLS termination handled by Nginx.

---

## Versioning

- Project version lives in [`VERSION`](VERSION) and must match `package.json`.
- Update [CHANGELOG.md](CHANGELOG.md) and [RELEASE.md](RELEASE.md) on every release.
- Tag releases using semantic versioning (`vX.Y.Z`) after CI passes.

---

## References

- [README.md](README.md) — overall setup and Makefile targets.
- [AGENTS.md](AGENTS.md) — agent roles and configuration.
- [SECURITY.md](SECURITY.md) — secrets handling and IAM guidance.

<!-- End file: REQUIREMENTS.md -->

## scripts/rollback.md

<!-- Begin file: scripts/rollback.md -->

# Rollback Runbook (§7)

1. **Identify the prior release tag.**

   ```bash
   git fetch --tags
   git tag --sort=-creatordate | head
   ```

2. **Checkout the previous release.**

   ```bash
   git checkout <previous-tag>
   ```

3. **Restore the matching index snapshot.**
   - Locate the snapshot in `indexes/snapshots/` stamped with the release timestamp.
   - Copy it over the active index:

     ```bash
     cp indexes/snapshots/<snapshot>.json indexes/atticus_index.json
     ```

4. **Re-pin configuration.**
   - Verify `pyproject.toml` matches the target tag.
   - Confirm embedding/LLM identifiers (`text-embedding-3-large`, `gpt-4.1`) in `atticus/config.py`.
5. **Smoke test with gold queries.**

   ```bash
   pytest evaluation/harness -k retrieval --maxfail=1
   ```

   Review `evaluation/runs/YYYYMMDD/` outputs for the top queries (nDCG@10, Recall@50, MRR).

6. **Log the rollback.**
   - Append the action to `CHANGELOG.md`.
   - Tag the rollback release (e.g., `v0.1.0-rollback1`) with a short summary of the trigger and outcome.

<!-- End file: scripts/rollback.md -->

## SECURITY.md

<!-- Begin file: SECURITY.md -->

# SECURITY — Atticus

This guide describes how to handle secrets, protect data, and report vulnerabilities when operating Atticus.

---

## Supported Versions

Security updates are guaranteed for the latest released minor and patch versions.
Older releases may receive fixes on a best‑effort basis only.

---

## Reporting a Vulnerability

If you discover a security issue:

1. **Do not** open a public GitHub issue.
2. Email the maintainers or your internal security contact with:
   - A clear description of the vulnerability and its potential impact.
   - Steps to reproduce or a proof‑of‑concept.
   - Affected versions and environment details.

We acknowledge reports within **3 business days** and coordinate a fix and disclosure timeline.

---

## Secrets Management

- **Never commit secrets** to source control.
- All configuration is read from `.env`. Host environment variables may override unless you set `ATTICUS_ENV_PRIORITY=env`.
- Recommended environment keys (minimum for production):
  - `OPENAI_API_KEY`
  - `CONTACT_EMAIL`
  - `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`
- Run diagnostics at any time:
  ```bash
  python scripts/debug_env.py
  ```
  This shows the source of each secret and a fingerprint for quick audits.

---

## Email Security (Amazon SES)

- Use **SES SMTP credentials** (not IAM access keys) for mail sending.
- The `SMTP_FROM` address must be a **verified SES identity** in the same AWS region.
- If your SES account is in **sandbox mode**, all recipients must be verified until production access is granted.
- Apply an IAM policy that **restricts sending** to approved addresses and your region only. Example:
  ```json
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": "ses:SendRawEmail",
        "Resource": "*",
        "Condition": {
          "StringEquals": {
            "ses:FromAddress": "atticus-escalations@yourdomain",
            "aws:RequestedRegion": "ap-southeast-2"
          }
        }
      }
    ]
  }
  ```
  ::: tip
  Update the address and region to match your verified SES identity (e.g. "us-east-1").
  :::

---

## Data Privacy and Logging

- **Redact PII** (personally identifiable information) in all logs and traces.
- The built‑in loggers `logs/app.jsonl` and `logs/errors.jsonl` already exclude known secret keys.
- Preserve stack traces for debugging but never log actual secret values.

---

## Contributor Guidelines

- Use environment variables and secret stores (e.g. AWS Secrets Manager) instead of hard‑coding credentials.
- Follow least‑privilege and data‑minimisation principles when accessing data sources.
- Before submitting code, run:
  ```bash
  make lint
  make typecheck
  ```
  to ensure nothing leaks into commits.

---

## Cross-References

- [AGENTS.md](AGENTS.md) — system architecture and escalation policies.
- [README.md](README.md) — quick-start and environment setup.
- [OPERATIONS.md](OPERATIONS.md) — day-to-day operations and evaluation metrics.

<!-- End file: SECURITY.md -->

## seeds/README.md

<!-- Begin file: seeds/README.md -->

# Seeds

The `seed_manifest.json` generated by `make seed` captures a lightweight summary of the
current CED corpus. It records document fingerprints, chunk counts, and the first set of
chunks (including SHA-256 hashes) so operators can bootstrap a development database
without requiring the full ingestion pipeline.

Running `make seed` will:

1. Load configuration from `.env`/`config.yaml`.
2. Parse up to 10 source documents from `content/` using the CED chunker.
3. Write `seeds/seed_manifest.json` containing the deduplicated chunk metadata.

The manifest is designed to be checked into CI as an artifact and referenced by
deployment pipelines or smoke tests that need deterministic seed data.

> **Note:** Table extraction relies on optional dependencies (`camelot`, `tabula`, OpenCV).
> If they are unavailable the script skips table metadata gracefully; install them for
> full fidelity in production environments.

## Contributor checklist

- Run `pytest tests/test_seed_manifest.py` to confirm the manifest structure and
  chunk metadata remain deterministic for CI.
- Execute `make seed` before opening a PR whenever documents inside `content/`
  change; commit the refreshed `seeds/seed_manifest.json` if the diff is
  intentional.
- Document any new optional dependencies required for seeding inside this file
  and `REQUIREMENTS.md` to keep onboarding clear.

<!-- End file: seeds/README.md -->

## STYLEGUIDE.md

<!-- Begin file: STYLEGUIDE.md -->

# STYLEGUIDE — Atticus

Consistent style makes the codebase easier to read, review, and maintain.
Follow these standards for all code and documentation.

---

## Python Code

- **Formatting**: Use [Ruff](https://docs.astral.sh/ruff/) with Black‑compatible style.

  ```bash
  make lint    # check style
  make format  # auto-format
  ```

- **Typing**: All public functions must be type‑hinted. Run `make typecheck` to validate.
- **Imports**: Organized automatically by Ruff on save.
- **Naming**: Use snake_case for functions and variables, PascalCase for classes.

---

## Markdown

- **Line length**: Wrap at about **100 characters** where practical.
- **Code blocks**: Use fenced blocks with a language tag for syntax highlighting. Example:

  ```python
  def example() -> None:
      print("Hello Atticus")
  ```

- **Tables**: Use GitHub‑flavored markdown tables for clear presentation of structured data.
- **Links**: Use relative paths for internal references, e.g. `[AGENTS.md](AGENTS.md)`.

---

## Commits

- Use **imperative mood** and include a scope.
  Examples:
  - `ui: add contact route`
  - `docs: update README for SES configuration`
- Reference related issues or task IDs when possible.

---

## Documentation

- Keep cross-links between [README.md](README.md), [AGENTS.md](AGENTS.md), and [OPERATIONS.md](OPERATIONS.md) accurate.
- Ensure examples and instructions match the latest code and Makefile targets.
- Update [CHANGELOG.md](CHANGELOG.md) when behaviour changes.

---

## Style Philosophy

- Strive for **clarity and minimalism** — no clever one-liners at the expense of readability.
- Ensure code and docs are understandable by both experienced developers and newcomers.

<!-- End file: STYLEGUIDE.md -->

## TODO.md

<!-- Begin file: TODO.md -->

# TODO - Atticus

All previously tracked items have been delivered and validated. See `TODO_COMPLETE.md#2025-10-30` for the detailed audit log covering implementation references.

There are no outstanding TODO entries at this time.

<!-- End file: TODO.md -->

## TODO_COMPLETE.md

<!-- Begin file: TODO_COMPLETE.md -->


# TODO — Completed / Obsolete

This file is the **permanent log of completed tasks**.
Each entry includes the completion date and commit reference for traceability.

The following items are done or no longer relevant and are recorded here for traceability.

## Completed
- **FND-001 → FND-008** (Audit): Next.js UI, proxy contracts, schema ownership, env scaffolding, request-id propagation, CI audits — delivered.
- **Ask Contract & Streaming**: `/api/ask` SSE endpoint and UI consumer normalised; error contracts include `request_id`.
- **Frontend Hygiene & Repo Structure**: Legacy FastAPI UI archived; canonical Next.js app; docs updated.
- **DX & Docs**: Makefile `quality` runs Python + Next gates + audits; pre-commit configured; release docs added.
- **Structured Logging**: Centralised logger with JSON output; instrumented key scripts.
- **Unified CLI**: `scripts/atticus_cli.py` with Makefile alias `atticus`.

## Obsolete / Superseded
- “Prisma duplicates and `Glossary.synonyms` type fix” — resolved in current schema/migrations.
- “Decide on Framer Motion” — kept as optional; AGENTS reflects this.
- “Archive web/static” — done; legacy moved under `archive/legacy-ui/`.
- “CONTENT_DIR → CONTENT_ROOT rename” — standardised across code/docs.
- “Rebuild evaluator harness” — present via tests and `eval` target.
- “Glossary API error normalisation” — implemented with `request_id`.

---

## 2025-10-10

- [x] Added model parser/resolver unit tests, retrieval filter coverage, API clarification regressions, UI integration tests, and a gated Playwright chat clarification flow — completed 2025-10-10 (this change set).
- [x] Documented model disambiguation behaviour in `AGENTS.md`, `README.md`, and `docs/ATTICUS_DETAILED_GUIDE.md`; updated `CHANGELOG.md`, and reconciled TODO status — completed 2025-10-10 (this change set).
- [x] Verified direct/unclear/multi-model acceptance criteria via automated tests and ensured `make quality` (lint, typecheck, pytest, Next build, ts audit) passes end-to-end — completed 2025-10-10 (this change set).

---

## 2025-09-21

- [x] Provided `.env.example` for local configuration scaffolding — completed 2025-09-21 (commit 5df0d73).
- [x] Delivered Dockerized stack (API/Nginx Dockerfiles, docker-compose workflow, healthchecks, Makefile targets) — completed 2025-09-21 (commit 5df0d73).
- [x] Published hardened `nginx.conf` for TLS termination and proxying to the FastAPI service — completed 2025-09-21 (commit 5df0d73).
- [x] Established single-node, containerized stack with minimal dependencies — completed 2025-09-21 (commit 3013a1a).
- [x] Removed Azure AD/SSO code paths and noted migration in README — completed 2025-09-21 (commit 3013a1a).
- [x] Pinned OpenAI defaults to `text-embedding-3-large` and `gpt-4.1` — completed 2025-09-21 (commit 3013a1a).
- [x] Created base repository structure (`atticus/`, `api/`, `ingest/`, etc.) — completed 2025-09-21 (commit 3013a1a).
- [x] Added `.editorconfig`, `.gitattributes`, `.gitignore`, and `.vscode` settings — completed 2025-09-21 (commit 3013a1a).
- [x] Implemented pre-commit hooks with `ruff`, `mypy`, `markdownlint-cli2` — completed 2025-09-21 (commit 3013a1a).
- [x] Adopted `pip-tools` for locked dependencies — completed 2025-09-21 (commit 3013a1a).
- [x] Pinned core libraries (`fastapi`, `uvicorn`, `pydantic`, etc.) — completed 2025-09-21 (commit 3013a1a).
- [x] Built parsers for PDF, DOCX, XLSX, and HTML with OCR support — completed 2025-09-21 (commit 3013a1a).
- [x] Implemented evaluation harness with baseline metrics and gold set — completed 2025-09-21 (commit 3013a1a).

## 2025-09-23

- [x] Added environment generator (`scripts/generate_env.py`) with `--force` flag — completed 2025-09-23.
- [x] Implemented SMTP mailer (`atticus/notify/mailer.py`) using `.env` — completed 2025-09-23.
- [x] Created API `/contact` route for escalation email (202 Accepted) — completed 2025-09-23.
- [x] Built API `/ask` endpoint returning `{answer, sources, confidence}` — completed 2025-09-23.
- [x] Integrated modern UI served by FastAPI templates and static mounts — completed 2025-09-23.
- [x] Added `examples/dev.http` with sample `/ask` and `/contact` requests — completed 2025-09-23.

## 2025-09-25

- [x] Verified README/AGENTS/OPERATIONS cross-links and fixed relative paths - completed 2025-09-25 (commit 2a3b760).
- [x] Added SES IAM policy region lock guidance to SECURITY.md and reinforced README cross-link - completed 2025-09-25 (commit 2a3b760).
- [x] TODO "SECURITY.md — env-only secrets; SMTP `From` allow-list; RLS examples." - completed 2025-09-25 (commit 2a3b760).

- [x] Reviewed repository documentation set and normalised coverage messaging - completed 2025-09-25 (commit cd280f8).
- [x] Published secure remote access playbook (Tailscale, Cloudflare Tunnel, SSH) - completed 2025-09-25 (commit cd280f8).

## 2025-09-27

- [x] Implemented shared JSON error schema for API responses with request ID propagation tests — completed 2025-09-27 (commit 6dbf0b8).
- [x] TODO "Error JSON contract" - completed 2025-09-27 (commit 6dbf0b8).
- [x] Verified API-served UI via automated tests (pytest) and captured guidance in ATTICUS detailed guide - completed 2025-09-25 (commit cd280f8).
- [x] Enabled optional hybrid reranker with `ENABLE_RERANKER` flag and documented behaviour - completed 2025-09-25 (commit cd280f8).
- [x] Updated README hero copy to spotlight Sales/tender acceleration messaging - completed 2025-09-25 (commit cd280f8).
- [x] Documented `/ask` request/response schema in docs/api/README.md - completed 2025-09-25 (commit cd280f8).
- [x] Added `SMTP_DRY_RUN` mailer branch with tests and surfaced behaviour in docs - completed 2025-09-25 (commit cd280f8).
- [x] Made pytest parallelism conditional on pytest-xdist availability - completed 2025-09-25 (commit cd280f8).
- [x] Retired the legacy Jinja2/Eleventy UI in favour of a Tailwind-powered Next.js app covering chat, admin, settings, contact, and apps — completed 2025-09-27.

## 2025-09-28

- [x] TODO "Sample Seed corpus — Add verification tests and contributor docs." — completed 2025-09-28 (commit 19bdc5d).
- [x] TODO "reports/ — Update evaluation pipeline to emit CSV/HTML artifacts." — completed 2025-09-28 (commit 19bdc5d).
- [x] TODO "reports/ — Configure CI to upload artifacts and document consumption workflow." — completed 2025-09-28 (commit 19bdc5d).
- [x] TODO "README.md — rewrite for Next.js/pgvector stack with Windows guidance and quick start." — completed 2025-09-28 (commit 5c4ff5e).
- [x] TODO "ARCHITECTURE.md — update diagrams/narrative for Next.js + SSE flow." — completed 2025-09-28 (commit 5c4ff5e).
- [x] TODO "OPERATIONS.md — document pgvector maintenance, CI parity, and dependency risk handling." — completed 2025-09-28 (commit 5c4ff5e).
- [x] TODO "TROUBLESHOOTING.md — capture Auth.js email flow, SSE mitigation, lint/format guidance." — completed 2025-09-28 (commit 5c4ff5e).
- [x] TODO "REQUIREMENTS.md — align runtime/tooling requirements with Next.js + Prisma stack." — completed 2025-09-28 (commit 5c4ff5e).
- [x] TODO "CI gates — align GitHub Actions + local make quality" — completed 2025-09-28 (commit 5c4ff5e).
  > Continue logging future completed tasks below, grouped by date, to maintain a clear historical record.

## 2025-09-29

- [x] TODO "Tests: ingestion/retrieval unit + integration suite, regenerate requirements lock." — completed 2025-09-29 (commit 04216be).

## 2025-09-30

- [x] TODO "TROUBLESHOOTING.md — Add pgvector + Prisma troubleshooting (extension enablement, migration drift)." — completed 2025-09-30 (commit b7779b8).

## 2025-10-04

- [x] TODO "`Makefile` — remove `ui` target (`http.server`); add Next.js scripts (`dev`, `build`, `start`); keep `api` until migration complete." — completed 2025-10-04 (commit b7779b8).

- [x] TODO "`api/routes/chat.py` and `api/routes/ask.py` — consolidate; ensure request_id & should_escalate; remove unused import in api/routes/**init**.py." — completed 2025-10-04 (commit 2af9f6e).
- [x] TODO "Dictionary/glossary admin — Design Prisma schema/API contracts for glossary records with approval workflow." — completed 2025-10-04 (commit 2bc7206).
- [x] TODO "Dictionary/glossary admin — Implement admin UI for propose/review/approve flows with RBAC checks." — completed 2025-10-04 (commit 2bc7206).

## 2025-10-05

- [x] TODO "`api/main.py` — drop Jinja2 templates/static mounts; stop serving `/` HTML; keep JSON APIs; Next.js owns UI." — completed 2025-10-05 (present in commit 9a7620b9; verified during backlog audit).
- [x] TODO "`ARCHITECTURE.md` & legacy `AGENTS.md` — replace FAISS/FastAPI mentions with references to this doc; mark migration phases." — completed 2025-10-05 (present in commit 9a7620b9; verified during backlog audit).

## 2025-10-10

- [x] TODO "Glossary Seed & Runbook" — completed 2025-10-10 (this PR aligns Prisma seeds, docs, and verification tests).

## 2025-10-11

- [x] TODO "Glossary UX Follow-through" — completed 2025-10-11 (added workflow sequence diagram, decision notes, and backlog links in `docs/glossary-spec.md`).

## 2025-10-12

- [x] TODO "RBAC Integration Coverage" — completed 2025-10-12 (Playwright reviewer/admin coverage, Next.js route RBAC tests, FastAPI admin token assertions, and `make quality` wiring).

## 2025-10-14

- [x] TODO "Phase 5 — Orphans & Structure Cleanup" — completed 2025-10-14 (FastAPI now sources its version from `VERSION`, docs highlight Next.js as the canonical UI, and release notes capture the separation of backend and frontend responsibilities).

## 2025-10-15

- [x] TODO "Admin Ops Console (Uncertain Chats, Tickets, Glossary)" — completed 2025-10-15 (introduced Prisma chat/ticket models, Next.js admin tabs, RBAC-aware API routes, and seeds/tests covering the reviewer/admin workflow).

## 2025-10-19

- [x] TODO "pgvector GUC Bootstrap" - completed 2025-10-19 (release 0.8.0 adds migrations and verification checks for `app.pgvector_lists`).
- [x] TODO "Version Parity Automation" - completed 2025-10-19 (release 0.8.0 ships `scripts/check_version_parity.py`, Makefile wiring, and docs).
- [x] TODO "Uncertain Chat Validation Flow" - completed 2025-10-19 (release 0.8.0 captures low-confidence chats, follow-up prompts, admin drawer UX, and audit events).
- [x] TODO "Dictionary (Glossary) Update Semantics" - completed 2025-10-19 (release 0.8.0 adds POST upsert/PUT updates, inline editing, and rag event auditing).

## 2025-10-30

- [x] Audited `TODO.md` and confirmed no outstanding backlog items remain; updated the file to reference the completion log.
- [x] Verified the model catalog in `indices/model_catalog.json` maps families ⇄ models/aliases as required by the backlog item.
- [x] Confirmed disambiguation utilities (`retriever/models.py`, `retriever/resolver.py`) and scoped retrieval (`retriever/service.py`) implement the parser/resolver tasks.
- [x] Checked the API and client flow updates in `api/routes/chat.py`, `app/api/ask/route.ts`, `lib/ask-contract.ts`, `lib/ask-client.ts`, and `components/AnswerRenderer.tsx` to ensure clarification + multi-answer behaviour is live.
- [x] Reviewed ingestion tagging updates in `ingest/pipeline.py` and supporting docs (`docs/api/README.md`, `README.md`) covering the model-family flows.

<!-- End file: TODO_COMPLETE.md -->

## TROUBLESHOOTING.md

<!-- Begin file: TROUBLESHOOTING.md -->

# TROUBLESHOOTING — Atticus

This guide covers common setup issues, ingestion problems, and quick diagnostics for Atticus deployments.

---

## Windows Setup Issues

- **Tesseract / Ghostscript**
  - Ensure both are installed and added to the system `PATH`.
  - If OCR or PDF parsing fails, verify their paths by running `tesseract --version` and `gswin64c --version`.

- **Python Wheels for 3.12**
  - If a dependency fails to build, rerun:

    ```bash
    pip install -r requirements.txt
    ```

    to rebuild compatible wheels.

- **Magic link smoke-test (PowerShell)**
  - Start the services:

    ```powershell
    make api
    make web-dev
    ```

  - Request a magic link and inspect the debug inbox:

    ```powershell
    Start-Process "http://localhost:3000/signin"
    Get-Content -Path "$env:AUTH_DEBUG_MAILBOX_DIR/*.eml"
    ```

  - If the link fails, confirm `NEXTAUTH_URL` and `AUTH_SECRET` are present in `.env` and restart both processes.

---

## PDF Parsing & Ingestion

- Prefer the **native text layer** for PDF extraction.
- OCR fallback is triggered only if no text layer is detected.
- After ingestion, verify that the number of chunks and token ranges match expectations in `logs/app.jsonl`.
- If duplicate chunks persist, inspect `seeds/seed_manifest.json` (generated by `make seed`) to confirm SHA-256 hashes differ.

Common ingestion checks:

- `.env` missing → run `python scripts/generate_env.py`.
- Unexpectedly small chunk counts → confirm `CHUNK_*` settings in `.env`.

---

## pgvector & Prisma

- **`pgvector extension not installed`** — run `make db.up` to ensure Postgres is online, then:

  ```bash
  make db.verify
  ```

  ```powershell
  make db.verify
  ```

  The script enables the extension when migrations run; if verification still fails, connect with psql and execute `CREATE EXTENSION IF NOT EXISTS vector;` manually before retrying `npx prisma migrate deploy`.

- **Embedding dimension mismatch** — export `PGVECTOR_DIMENSION` to the value used by the ingestion pipeline (default `3072`) and re-run `make db.verify`. Update `atticus/config.py` if the embeddings service changes dimension.
- **IVFFlat index missing or stale** — rerun migrations (`npx prisma migrate deploy`) and then `make db.verify`. The migration recreates `idx_atticus_chunks_embedding` with the configured `PGVECTOR_LISTS` default (`100`).

---

## SMTP / Email Escalation

- Verify all SMTP settings in `.env`: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`, `CONTACT_EMAIL`, and `SMTP_ALLOW_LIST`.
- Check network/firewall rules if emails do not send.
- Use the built‑in test:

  ```bash
  make smtp-test
  ```

_Error codes:_ `recipient_not_allowed` or `sender_not_allowed` indicate allow-list misconfiguration. Update `SMTP_ALLOW_LIST` to include the relevant address or domain.

---

## FastAPI / UI

- If the API fails to start:
  - Run `make lint` and `make typecheck` to catch syntax or typing errors.
  - Check logs in `logs/errors.jsonl` for stack traces.
- Confirm the UI is accessible at `http://localhost:3000/` via `make web-dev`.
  If the UI has been separated again, reintroduce a dedicated make target and update port mapping.

## Streaming `/api/ask` Issues

- **No stream events received**
  - Ensure the UI or client sends `Accept: text/event-stream`. The shared helper in `lib/ask-client.ts` enforces the header.
  - Verify `RAG_SERVICE_URL` points to the FastAPI service. On Windows PowerShell:

    ```powershell
    Invoke-WebRequest -UseBasicParsing -Method Post `
      -Uri "$env:RAG_SERVICE_URL/ask" `
      -Body '{"question":"ping"}' `
      -ContentType 'application/json'
    ```

- **502 or `upstream_unreachable` errors**
  - Confirm `make api` is running and reachable at the configured port.
  - Inspect the FastAPI logs for request IDs logged via `ask_endpoint_complete`.

- **SSE connection closes immediately**
  - Disable corporate proxies that buffer responses; SSE requires a raw streaming connection.
  - Set `NODE_OPTIONS=--enable-source-maps` when debugging to surface the originating stack trace inside the Next route handler.

---

## Lint / Format Failures

- **Prettier differences** — run `npm run format` (writes) or `npm run format:check` (CI-friendly). Tailwind class order is enforced via `prettier-plugin-tailwindcss`.
- **ESLint violations** — run `npm run lint`. The configuration uses the tailwindcss plugin; ensure utility classes flow through the `cn` helper.
- **Ruff or mypy failures** — use `make format` (auto-fix) and `make typecheck` to reproduce Python findings.
- **Full parity check** — `make quality` mirrors CI across Python + Next.js tooling.

---

## Pre-commit hook failures

Install hooks with `pre-commit install`. To re-run everything after fixing issues:

```bash
pre-commit run --all-files --show-diff-on-failure
```

If local Node tooling drifts, reinstall via `npm install` and retry.

---

## Dependency installation failures

- Capture Python failures with `mkdir -p logs/install && pip-sync requirements.txt 2>&1 | tee logs/install/pip-sync.log` and attach the log to incident notes.
- Capture Node failures with `mkdir -p logs/install && npm install --verbose 2>&1 | tee logs/install/npm-install.log`; redact tokens before sharing.
- Archive both logs under `logs/install/` for the current date and reference them from the audit trail.

---

## npm audit warnings

`npm audit` currently reports a critical Next.js middleware advisory (GHSA-f82v-jwr5-mffw) plus moderate issues in Next.js, esbuild, vite, and vitest. No fixed versions are available as of 2025-09-28; monitor upstream releases and capture justifications in `reports/ci/npm-audit-latest.json` (see [OPERATIONS.md](OPERATIONS.md#dependency-risk-exceptions)).

---

## Rate Limiting & 429 Responses

- `429 rate_limited` responses mean the user/IP exceeded `RATE_LIMIT_REQUESTS` within `RATE_LIMIT_WINDOW_SECONDS`.
- Inspect `logs/app.jsonl` for `rate_limit_blocked` entries; identifiers are hashed (first 12 hex chars) for privacy.
- Adjust thresholds in `.env` or introduce per-tenant overrides before raising limits globally.
- `/admin/metrics` exposes rate-limit counters (`blocked`) alongside query/escalation statistics.

---

## Index and Retrieval Issues

- **Rollback to a known-good index**:

  ```bash
  python scripts/rollback.py --manifest indices/manifest.json
  ```

- **Smoke test after rollback**:

  ```bash
  make eval
  ```

- If retrieval quality drops (low nDCG or Recall), re-run `make ingest` and re-check chunking settings.

---

## Quick Diagnostic Commands

| Action                         | Command                                    |
| ------------------------------ | ------------------------------------------ |
| Check environment fingerprints | `python scripts/debug_env.py`              |
| Tail live logs                 | `tail -f logs/app.jsonl`                   |
| Check errors only              | `tail -f logs/errors.jsonl`                |
| Fetch metrics dashboard        | `curl http://localhost:8000/admin/metrics` |
| Full end-to-end smoke test     | `make e2e`                                 |

---

## References

- [README.md](README.md) — installation and setup
- [OPERATIONS.md](OPERATIONS.md) — detailed runbooks and evaluation metrics
- [SECURITY.md](SECURITY.md) — secret handling and IAM policy examples

<!-- End file: TROUBLESHOOTING.md -->
