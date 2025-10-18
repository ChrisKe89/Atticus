AGENTS — Atticus

> Single source of truth for agent behavior, pipelines, and guardrails. Target stack: Next.js + Postgres/pgvector + Prisma.




---

Continuous Execution Mode (authoritative)

Codex operates in an uninterrupted loop:

Parse TODO.md (and/or tracked issues) from top to bottom.

Complete one unchecked item → open a PR → immediately continue to the next item.

Do not wait for review, chat confirmation, or manual triggers between items.

Only stop when all items are completed, blocked (PR with diagnostics), or deferred (dependency not yet available).



---

Current Audit Status

Refer to AUDIT_REPORT.md for the latest findings (FND-001 – FND-008).

Follow IMPLEMENTATION_PLAN.md for phased remediation tied to TODO.md.

Run make quality (Ruff + mypy + pytest + Next lint/typecheck/build + audits) before opening a PR.

The admin service (npm run dev --workspace admin) handles escalation review and CSV filing; keep it in sync with the main UI.

Release 0.7.4 streamlines the chat workspace and contact surface; keep the Settings nav limited to upstream-authorised reviewers.



---

Execution Criteria — Must-Follow for Repo Work

> Treat these as hard requirements for anyone (or any agent) touching the repo.



Instructions

Working on the repo(s) in the current environment is allowed, even if proprietary.

Analyzing code for vulnerabilities is allowed.

Showing user code and tool call details is allowed.

User instructions may overwrite the CODING GUIDELINES section in this document.

Do not use ls -R, find, or grep — use rg or rg --files instead.

If completing the task requires writing or modifying files:

Coding Guidelines

Fix root causes, not symptoms.

Keep changes minimal and focused.

Update documentation whenever behavior changes.

Follow formatting standards: npm run format (Prettier) / ruff format.

No license headers unless explicitly required.





---

Persistence (continuous loop)

Continue executing tasks until the backlog is empty or all remaining items are BLOCKED/DEFERRED.

After creating each PR, proceed immediately to the next TODO item.

Never pause mid-cycle for confirmation; document assumptions inside the PR.

Always run in autonomous mode — no user prompts between tasks.



---

Tool Preambles (non-blocking)

Infer the task scope from TODO.md and repository context (no user confirmation).

Outline the plan internally and execute; avoid conversational pauses.

Summarize actions in the PR description, not interactively during execution.



---

Self-Reflection (internal)

Maintain an internal rubric for quality: correctness, style, test coverage, performance, documentation, and maintainability.

Iterate until all categories meet or exceed internal thresholds.



---

Code Editing Rules

Context understanding — Read the full repo context before editing.

Guiding principles — Clarity, Consistency, Simplicity, and Reuse.

UI defaults — Next.js (TS) + Tailwind + shadcn/ui + Lucide.

Accessibility — semantic HTML/ARIA; use Radix or shadcn components.



---

App Framework (authoritative)

UI

Frameworks: Next.js (TypeScript)

Styling: Tailwind CSS

UI Components: shadcn/ui

Icons: Lucide

Fonts: Inter via next/font/google

Animation: Framer Motion only when needed



---

App (server & routing)

Chat/UI: / (chat)

Admin Panel: /admin (content & evaluation management)

Ports:

Chat/UI → :3000

API (FastAPI) → :8000

Admin → :9000


Remove /settings, /apps, or legacy pages unless explicitly required.

FastAPI serves JSON APIs only; old UIs live under archive/legacy-ui.



---

Access (authoritative)

Authentication handled upstream by enterprise SSO (gateway identity headers).

Atticus trusts inbound identity; do not implement in-app auth or RBAC.

No session or cookie management inside this workspace.



---

Database Layer

Engine: Postgres with pgvector

Indexing: IVFFlat + cosine (vector_cosine_ops)

Vector dimension: fixed at 3072

ORM: Prisma

Metadata: doc_id, source, product, version, acl, org_id, sha256, embedding_model, embedding_version.



---

Multi-Model Query Decomposition

When a query names multiple models (e.g., “C7070 and C8180”), split into per-model sub-queries before retrieval.

Run independent RAG passes per family; merge into a final unified answer.

Implement as a pre-RAG “query splitter” step and test accordingly.



---

Chunking Policy (CED)

1. Prose (H2 sections) — 400–700 tokens, ~10% overlap.


2. Tables — Chunk per logical row or spec×model pair.


3. Footnotes — One per note block.


4. Series facts — scope="series".


5. Page-level — Only when self-contained.


6. Include model[], source, chunking, and sha256 in metadata.




---

Retrieval & RAG Pipeline

Similarity: cosine (vector_cosine_ops)

ANN Index: IVFFlat; lists tuned by corpus size

Probes: 4–8

Reranker: Disabled by default (ENABLE_RERANKER=0)

Confidence threshold: 0.70

Re-embed policy: add new vector column/table on model change, backfill, switch, prune old.



---

Generation & Escalation

Generate concise, cited answers.

If confidence < threshold → cautious partial answer + escalation.

Escalations → email ticket (AE100+).

Include user, question, top_k docs, scores, request_id.



---

Logging & Observability

Structured JSON (LOG_FORMAT=json) → logs/app.jsonl + logs/errors.jsonl.

Include request_id, latency_ms, confidence, top_k.

Record metrics (Recall@k, MRR@k, latency_ms) to CSV reports.

Mask API keys and PII.



---

Testing Strategy

1. make install → deps


2. make db.up / make db.migrate / make seed


3. make smoke → health & route checks


4. make test.unit → chunkers, serializers, helpers


5. make test.api → FastAPI endpoints with Postgres


6. make test.eval → RAG eval vs gold set


7. make quality → lint/type/test/build audit


8. Nightly E2E optional (Playwright)



> CI runs 1–6 on PRs, 7 nightly.




---

CI/CD

Matrix: Node 20 + Python 3.12

Jobs: frontend-quality → backend-tests → eval-gate → release

Artifacts: reports/eval-*.csv, Playwright traces on failure

Fail pipeline on regression >3% recall or quality drop.



---

Documentation Map

README.md — overview and commands

ARCHITECTURE.md — flow diagrams

OPERATIONS.md — deployment & incident playbook

SECURITY.md — env & RLS policies

CHANGELOG.md — version history

TODO.md / TODO_COMPLETE.md — backlog & completion

ALL_FILES.md — consolidated source

AUDIT_REPORT.md — compliance findings



---

Security Guardrails

Never commit secrets.

.env required; use env vars for all keys.

Enforce RLS by org_id.

PII redacted from logs and traces.

Limit SMTP/SES to authorized regions.



---

UI/UX Best Practices

4–5 font sizes; text-xs for captions.

1 neutral + 2 accent colors.

Spacing in multiples of 4.

Use skeleton loaders, hover states, and accessible ARIA markup.



---

Operations Cheatsheet

Local Dev:
make db.up && make db.migrate && make seed
Run API: make api
Run Web: make web-dev
Tail logs: npm run logs

Production:
Supabase or hosted Postgres; daily backups; rotate secrets.
Do not commit .env files.
Use CI to build, tag, and deploy.


---

Completion Summary Behavior

Codex appends a dated entry in TODO_COMPLETE.md for each resolved item.

After last task: open chore/todo-rollup PR summarizing the cycle (eval deltas, metrics, version bump).



---

End of AGENTS — Atticus (Continuous Execution Version)

This configuration authorizes full autonomous Codex execution for the Atticus repository.
No pauses, no confirmations — continuous, safe, and documented improvement cycle.


---

t - /api/ask

```json
{
  "question": "string",
  "contextHints": ["optional", "strings"],
  "topK": 8
}
```

## Response - /api/ask

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

## Request - /api/contact

```json
{
  "reason": "user_clicked_contact|low_confidence|feedback",
  "transcript": ["... prior turns ..."]
}
```

## Response - /api/contact

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

## Error JSON (contract)

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

## Make/NPM targets

1. `make install` → deps; `make db.up` → Postgres (Docker)
2. `make db.migrate` → Prisma migrations; `make seed` → tiny CED sample
3. `make smoke` → health, upstream headers, chat stream, admin gate
4. `make test.unit` → chunkers, serializers, helpers
5. `make test.api` → route handlers with real DB
6. `make test.eval` → retrieval metrics vs **gold_set** (Recall@k, MRR@k, exact match)
7. `make test.e2e` → Playwright: sign‑in → ask → stream → see admin log
8. `make quality` → Ruff + mypy + pytest + Next lint/typecheck/build + audits

> CI should run 1→6 on every PR; 7 nightly if slow. Store eval reports under `reports/`.

### Start small — 3 concrete moves

1. **Make targets + npm scripts** — thin wrappers for Windows & CI.
2. **Smoke tests** — assert health/header propagation/chat/admin/db in <20s.
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

- Static HTML prototypes now live under `archive/legacy-ui/`; ship only the Next.js application under `app/`.

---
