# TODO - Atticus (Authoritative Active List)

This file is the **single source of truth** for active tasks.
Items completed are moved to [ToDo-Complete.md](ToDo-Complete.md).
Tasks marked **[Codex]** are ideal for automation.

**A. Code changes required to align with this AGENTS spec**

1. **Replace FAISS with Postgres/pgvector** — remove `atticus/faiss_index.py` and file‑index configs; add DB + vector index config; write to `documents/chunks` with `embedding VECTOR(D)`; create `pgvector` extension and **IVFFlat** index; set `probes`.
2. **Unify `/api/ask` route & response** — keep one route returning `{answer,sources,confidence,request_id,should_escalate}`; remove duplicate module; fix `api/main.py` mounts; ensure `request_id` present.
3. **Auth.js + RBAC** — introduce email magic link; gate `/admin` & sensitive APIs by role; add RLS keyed by `org_id`; replace ad‑hoc dictionary endpoints with role‑checked admin APIs.
4. **Ingestion — CED chunkers** — implement prose/table/footnote chunkers; serialize table rows; stamp rich metadata; compute `sha256` for de‑dup.
5. **Email escalation** — keep SMTP, load sender/region from env; add `SMTP_FROM` allow‑list; include trace payload (user/chat/message ids, top‑k docs & scores, question).
6. **Structured logs + metrics** — keep `logs/app.jsonl` & `logs/errors.jsonl`; add per‑turn trace IDs; redact PII; expand metrics (retrieval/latency histograms).
7. **Rate limiting** — per user/IP limiter with tests; expose counters in admin.

**B. Existing markdown/docs to update**

1. **README.md** — switch FastAPI/FAISS/Eleventy → Next.js/pgvector/Prisma/Auth.js; include Windows‑friendly commands & `.env` examples.
2. **ARCHITECTURE.md** — diagrams for pgvector flows + SSE; remove Jinja/Nunjucks.
3. **OPERATIONS.md** — DB backup/restore; RLS policy examples; pgvector DDL and `probes` docs.
4. **TROUBLESHOOTING.md** — Auth.js email flow; pgvector extension issues; Prisma migration conflicts; SSE timeouts.
5. **REQUIREMENTS.md** — add Postgres + Prisma; deprecate FAISS/Jinja2; keep Windows notes.
6. **SECURITY.md** — env‑only secrets; SMTP `From` allow‑list; RLS examples.

**C. Items to carry into AGENTS (non‑conflicting)**

1. **CI gates** — keep lint/test/eval/release; adjust for TS/Next.js later; preserve eval gate.
2. **Error JSON contract** — standardize across the API.
3. **Dictionary/glossary admin** — keep concept; migrate storage to DB; surface in Admin.

**D. Documentation depth improvements**

1. **Glossary** admin page spec + DB schema with reviewer propose → admin approve flow.
2. **Sample Seed** corpus (CED) + `make seed` target.
3. **reports/** with retrieval eval CSV + small HTML summary; publish in CI.

**E. File‑specific TODOs from audit**

1. `atticus/config.py` — remove `faiss_index_path`/file‑index fields; add `DATABASE_URL`, `EMBEDDING_DIM`, vector tunables (lists/probes).
2. `atticus/faiss_index.py` — delete; replace with pgvector DAO (CRUD for `documents/chunks`, cosine search).
3. `api/main.py` — drop Jinja2 templates/static mounts; stop serving `/` HTML; keep JSON APIs; Next.js owns UI.
4. `api/routes/chat.py` and `api/routes/ask.py` — consolidate; ensure `request_id` & `should_escalate`; remove unused import in `api/routes/__init__.py`.
5. `Makefile` — remove `ui` target (`http.server`); add Next.js scripts (`dev`, `build`, `start`); keep `api` until migration complete.
6. `requirements.in` — remove `faiss-cpu`, `jinja2`; add `psycopg[binary]` for local Python dev until TS/Next.js replaces Python API.
7. `ARCHITECTURE.md` & legacy `AGENTS.md` — replace FAISS/FastAPI mentions with references to this doc; mark migration phases.

## Uncategorized

* [ ] Blocked: see [REQUIREMENTS.md](REQUIREMENTS.md#code-review-scope) — Define scope, depth, and deliverables for the end-to-end code review.
* [ ] Blocked: see [REQUIREMENTS.md](REQUIREMENTS.md#backlog-sweep-process) — Provide expectations for how aggressively to clear README/TODO deltas.

## Product & Audience

*(No active items.)*

## Retrieval

*(No active items.)*

## API & UI


## Tooling

*(No active items.)*

## Documentation

* [ ] Blocked: see [REQUIREMENTS.md](REQUIREMENTS.md#hero-graphic-asset) — Supply the approved README hero graphic assets.

## Future Enhancements (from EXAMPLES_ONLY) and can be ignored for now

* [ ] **[Codex]** Evaluate Socket.IO progress streaming so ingestion/eval status updates mirror `EXAMPLES_ONLY/socketio.mdx`.
* [ ] **[Codex]** Prototype a knowledge base crawling UI and background scheduler akin to `EXAMPLES_ONLY/crawling-configuration.mdx`.
* [ ] **[Codex]** Investigate MCP tool integration to orchestrate cross-service workflows (see `EXAMPLES_ONLY/mcp-overview.mdx`).
* [ ] **[Codex]** Explore collaborative project room management patterned on `EXAMPLES_ONLY/projects-overview.mdx`.
* [ ] **[Codex]** Outline observability dashboards inspired by `EXAMPLES_ONLY/server-monitoring.mdx` (service health, queue depth, alerts).

---

> Keep this list accurate and up to date. Once a task is finished, move it to [ToDo-Complete.md](ToDo-Complete.md) with the completion date and relevant commit ID.
