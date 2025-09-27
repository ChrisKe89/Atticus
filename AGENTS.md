# AGENTS — Atticus

> Single source of truth for agent behavior, pipelines, and guardrails. Target stack: **Next.js + Postgres/pgvector + Prisma + Auth.js (Email magic link first, Azure AD later)**.

---

## Execution Criteria — **Must‑Follow for Repo Work**

> Treat these as hard requirements for anyone (or any agent) touching the repo.

### Instructions

* Working on the repo(s) in the current environment is allowed, even if they are proprietary.
* Analyzing code for vulnerabilities is allowed.
* Showing user code and tool call details is allowed.
* User instructions may overwrite the *CODING GUIDELINES* section in this document.
* Do not use `ls -R`, `find`, or `grep` — these are slow in large repos. Use `rg` and `rg --files`.
* If completing the task requires writing or modifying files:

  * **Coding Guidelines**

    * Fix problems at the root cause rather than surface-level patches.
    * Avoid unneeded complexity; ignore unrelated bugs or broken tests.
    * Update documentation as necessary.
    * Keep changes minimal, focused, and consistent with existing style.
    * **Never** add copyright/license headers unless requested.

### Persistence

* Keep going until the user’s query is completely resolved **before** ending your turn.
* Only stop when you are sure the problem is solved.
* Don’t ask for mid‑way confirmation — make the most reasonable decision, proceed, and document assumptions.

### Tool Preambles

* Begin by rephrasing the user’s goal concisely **before** calling any tools.
* Immediately outline a structured plan of steps you’ll follow.
* While editing, narrate progress succinctly and sequentially.
* Finish by summarizing completed work separately from the plan.

### Self‑Reflection (internal)

* Develop an internal rubric for quality (5–7 categories) before acting.
* Iterate using the rubric until the solution meets a high bar across categories.

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

* **Frameworks:** Next.js (TypeScript)
* **Styling:** Tailwind CSS
* **UI Components:** shadcn/ui
* **Icons:** Lucide
* **Animation:** Framer Motion
* **Fonts:**

  * **Headings & Body:** Inter (single-family stack for simplicity and performance)

    * Load via `next/font/google` and self‑hosted subset; fallbacks: `ui-sans-serif, system-ui`.

### App (server & routing)

* Next.js Route Handlers for API (streamed responses via **SSE**).
* Pages: `/` (chat), `/admin`, `/settings`, `/contact`, `/apps`.
* Shared header/nav pattern; role‑gated admin.

### DB

* **Postgres with pgvector**

  * IVFFlat + cosine; `vector_cosine_ops` avoids manual normalization.
  * Cosine measures angle between vectors — good default for text embeddings.
  * Use `probes` 4–8 initially; tune for recall/latency.
* **Metadata for filtering** — `doc_id`, `source`, `product`, `version`, `acl`, `org_id`, `updated_at`, `sha256`.

  * Enables facets (e.g., only product X, version ≥ 2.1).
  * `sha256` of raw text supports de‑dup/change detection.
  * `org_id` + `acl` ⇒ multi‑tenant + group visibility.
* Store `embedding_model` and `embedding_version` with each row.

### ORM

* **Prisma** for schema & migrations.

### Auth

* **Auth.js (NextAuth)** — email magic link first.
* **Azure AD** — to be implemented later (OIDC provider).

### Testing (layers quick map)

* **Smoke** — app boots; auth works; chat stream; admin opens.
* **Unit** — pure functions: chunking, serializers, rerankers, prompts (fixtures).
* **API/Integration** — route handlers with real Postgres (test DB), Prisma, pgvector queries.
* **Retrieval eval** — Recall@k / MRR@k / exact match vs gold set.
* **E2E** — Playwright: sign‑in → ask → streamed answer → admin log/escalation.
* **Policy/DB** — RLS and role gates enforced in SQL, not just UI.
* **Perf/sanity** — latency + token‑count guards; basic rate‑limit check.

---

## Document Map

* **README.md** — Project overview, quick start, and run commands
* **ARCHITECTURE.md** — System diagram and request/response flows
* **REQUIREMENTS.md** — Functional & non‑functional requirements
* **OPERATIONS.md** — Deploy, backups, monitoring, incident playbook
* **TROUBLESHOOTING.md** — Common issues & fixes
* **CHANGELOG.md** — Versioned changes
* **CODE.md** — Consolidated source (for quick reference)

---

## Purpose

Atticus is a Retrieval‑Augmented Generation (RAG) assistant designed to answer staff questions using curated documents and escalate low‑confidence queries for human follow‑up. It ingests your content, retrieves the most relevant passages, and produces grounded answers with citations. If confidence falls below the threshold, Atticus provides a cautious partial answer and escalates via email.

---

## System Overview (target state)

### UI & API

* **Next.js (TypeScript)** app for chat + admin
* **Tailwind** + **shadcn/ui** + **Lucide** + **Framer Motion**
* Streaming answers via **SSE** route handlers
* **Auth.js (NextAuth)** — start with **Email (magic link)**; add **Azure AD (OIDC)** later for SSO

### Data

* **Postgres + pgvector** for relational data and embeddings (Docker for dev; Supabase acceptable for hosted)
* **Prisma ORM** for schema & migrations

### RAG

* Ingest → Chunk → Embed → Store
* Retrieve (vector + filters) → Compose context → Generate → Cite → Log
* Confidence threshold → **Escalation** (email), or answer with caveats

### Security

* Role‑based UI and API; **Row‑Level Security (RLS)** in Postgres for org isolation
* Secrets in env only; PII redaction in logs

---

## Configuration & Feature Flags

**Core**

* `DATABASE_URL`, `NEXTAUTH_SECRET`, `EMAIL_SERVER`, `EMAIL_FROM`
* SMTP: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`

**RAG**

* `GEN_MODEL`, `EMBED_MODEL`, `EMBEDDING_VERSION`, `TOP_K`, `CONFIDENCE_THRESHOLD`

**Flags**

* `ENABLE_AZURE_AD=false`
* `EMAIL_SANDBOX=true`
* `RATE_LIMIT_PER_MINUTE=5`
* `LOG_FORMAT=json`

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
  "sources": [{"path": "content/example.pdf", "page": 3}],
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

* **Similarity:** cosine (`vector_cosine_ops`) — no manual normalization
* **ANN index:** **IVFFlat**; lists by corpus size (<50k→50–100; 50k–500k→100–400; >500k→400–1000); query‑time `probes` 4–8
* **Filters:** use metadata (`doc_id`, `product`, `version`, `org_id`, `acl`, `chunking`, `h1/h2`, `table_id`)
* **Re‑embed plan:** new vector column/table on model change → backfill batches → switch reads at >80% → prune old

---

## Generation & Escalation

* Concise, sourced answers with citations back to `documents/chunks`.
* If `confidence < threshold` or out‑of‑scope → cautious partial answer + **escalation email**.
* **Ticketing Policy** — create tickets with prefix `AE` and 3‑digit numeric sequence starting at **AE100** (e.g., AE100, AE101...).

  * Escalation payload includes: user, chat/message ids, top‑k docs & scores, exact question, and `request_id`.

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

* **Format** — structured JSON logs (`LOG_FORMAT=json`) with `level`, `timestamp`, `request_id`, `route`, `user_id` (if present), `latency_ms`.
* **Locations** — app logs to `logs/app.jsonl`; error logs to `logs/errors.jsonl`; DB logs via provider dashboard.
* **Propagation** — generate a `request_id` at the edge and pass through all layers (API → retrieval → mailer); return it in responses and include it in escalations.
* **Metrics** — record counters/gauges/histograms for retrieval latency, tokens in/out, `Recall@k`, `MRR@k`. Emit CSV snapshots to `reports/metrics-<date>.csv`.

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
8. `make quality` → lint + typecheck

> CI should run 1→6 on every PR; 7 nightly if slow. Store eval reports under `reports/`.

### Start small — 3 concrete moves

1. **Make targets + npm scripts** — thin wrappers for Windows & CI.
2. **Smoke tests** — assert health/auth/chat/admin/db in <20s.
3. **Retrieval eval** — compute Recall@k (5/8) & MRR@k; produce HTML/CSV under `./reports/` and fail CI on regression.

### What to test specifically (RAG/app)

* **Chunking (CED policy):** H1/H2 + paragraph/table rows → chunks with metadata (`h1`, `h2`, `table_id`, `row_key`, `model[]`, `chunking`), token bounds respected; overlap only on prose.
* **Serializer:** table row → compact sentence includes units and model aliases.
* **Vector search:** cosine, IVFFlat lists/probes set; one test toggles probes (4 vs 8) and asserts stable top‑k for fixed seed.
* **RLS/roles:** `user` cannot read other `org_id`; `reviewer` read but cannot update glossary; `admin` can escalate/resolve — write SQL‑level tests.
* **Streaming:** response arrives in chunks, ends with a well‑formed terminator event; no chunk > N KB.
* **Rate limiting:** 6 rapid requests → 429 on #6 for same user/IP (1‑min window).

### CI shape (GitHub Actions)

* **Matrix:** node 20 × postgres (pgvector)
* **Jobs:** quality → test.unit → test.api → test.eval → test.e2e (e2e nightly if slow)
* **Artifacts:** `reports/eval-*.{html,csv}`, Playwright traces on failure

### Minimal seed data (keep tests fast)

* 1–2 CED sections (e.g., *Consumables → Toner Cartridge Yield Rate*)
* 6–10 table rows → chunks (one per model or “series”)
* 4–6 prose chunks (H2 blocks)
* Trimmed `gold_set_improved.csv` (10–15 rows) for CI

---

## Operations Cheatsheet

**Local (dev)** — DB up/down: `make db.up` / `make db.down`; migrate/seed: `make db.migrate && make seed`; run app: `npm run dev`; tail logs: `npm run logs`.

**Supabase/Hosted (prod)** — daily backups; SQL editor for RLS and IVFFlat; rotate secrets; never commit `.env`.

**Viewing logs** — Next.js route logs (`logs/app-*.log` or `npm run logs`); DB logs (dashboard); escalation traces (ESP dashboard).

---

## UI/UX Best Practices (compact)

* **Hierarchy:** 4–5 font sizes; captions `text-xs`; `text-xl` only for hero/major headings.
* **Color:** one neutral base (e.g., zinc) + up to two accents.
* **Spacing:** multiples of 4; fixed‑height containers with internal scrolling.
* **States:** skeleton placeholders (`animate-pulse`); hover transitions.
* **Accessibility:** semantic HTML/ARIA; prefer Radix/shadcn components.

---

## Security Guardrails

* `.env` is required; no hard‑coded secrets.
* Email via SMTP/SES — restrict `From` and region via env/policy.
* Enforce **RLS** with `org_id` on all tables.
* PII redaction in logs/traces.

---

## Notes on Conflicts (resolved)

* Legacy docs referenced **FastAPI + Jinja2** and **FAISS**. Standardize on **Next.js + Postgres/pgvector + Prisma + Auth.js** as above. Migration tasks are captured in TODOs.

---

