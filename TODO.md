# TODO - Atticus (Authoritative Active List)

This file is the **single source of truth** for active tasks.
Items completed are moved to [ToDo-Complete.md](ToDo-Complete.md).

**A. Code changes required to align with this AGENTS spec**

1. **Replace FAISS with Postgres/pgvector** — remove `atticus/faiss_index.py` and file-index configs; add DB + vector index config; write to `documents/chunks` with `embedding VECTOR(D)`; create `pgvector` extension and **IVFFlat** index; set `probes`.
   - [ ] Inventory FAISS usage across code, scripts, and configs to scope the migration surface.
   - [ ] Design `documents`/`chunks` schema with pgvector columns and generate Prisma/SQL migrations.
   - [ ] Update ingestion pipeline to persist embeddings into Postgres and snapshot metadata in the new format.
   - [ ] Implement pgvector-backed retrieval DAO and remove FAISS loading/saving paths.
   - [ ] Drop FAISS dependencies/configuration (code, requirements, docs) and backfill unit/integration tests.
2. **Unify `/api/ask` route & response** — keep one route returning `{answer,sources,confidence,request_id,should_escalate}`; remove duplicate module; fix `api/main.py` mounts; ensure `request_id` present.
   - [ ] Audit callers (frontend, tests, SDKs) relying on `chat.py` vs `ask.py` implementations.
   - [ ] Consolidate logic into a single handler that always emits the canonical contract.
   - [ ] Remove redundant modules/imports and adjust router wiring plus schema exports.
   - [ ] Update client code, fixtures, and tests to match the unified endpoint.
3. **Auth.js + RBAC** — introduce email magic link; gate `/admin` & sensitive APIs by role; add RLS keyed by `org_id`; replace ad-hoc dictionary endpoints with role-checked admin APIs.
   - [ ] Integrate Auth.js into the Next.js app (dependencies, `/api/auth` routes, session provider).
   - [ ] Implement email magic-link provider and persistence for sessions/users.
   - [ ] Define role model (`user`, `reviewer`, `admin`) and apply row-level security policies in Postgres/Prisma.
   - [ ] Update API route guards and admin UI components to enforce role checks.
   - [ ] Add auth/RBAC unit, integration, and Playwright coverage.
4. **Ingestion — CED chunkers** — implement prose/table/footnote chunkers; serialize table rows; stamp rich metadata; compute `sha256` for de-dup.
   - [ ] Capture detailed chunking rules + examples from CED policy.
   - [ ] Implement prose/table/footnote chunker utilities with metadata enrichment and SHA-256 hashing.
   - [ ] Adapt pipeline reuse/backfill logic to respect hashed content and new metadata fields.
   - [ ] Add fixtures/tests covering chunk shapes, metadata, and dedupe behaviour.
5. **Email escalation** — keep SMTP, load sender/region from env; add `SMTP_FROM` allow-list; include trace payload (user/chat/message ids, top-k docs & scores, question).
   - [ ] Document required env vars and build allow-list configuration.
   - [ ] Enforce sender/region validation and return actionable errors when misconfigured.
   - [ ] Extend escalation payload with trace data and ensure redaction where needed.
   - [ ] Update docs/tests to cover dry-run, failure, and success paths.
6. **Structured logs + metrics** — keep `logs/app.jsonl` & `logs/errors.jsonl`; add per-turn trace IDs; redact PII; expand metrics (retrieval/latency histograms).
   - [ ] Extend logging helpers to inject request IDs, latency, and contextual metadata.
   - [ ] Introduce metrics emission (histograms/counters) for retrieval, latency, and token usage.
   - [ ] Sweep codebase to ensure sensitive fields are redacted before logging.
   - [ ] Update documentation and tests to validate logging/metrics expectations.
7. **Rate limiting** — per user/IP limiter with tests; expose counters in admin.
   - [ ] Choose limiter strategy (middleware + store) and define configurable thresholds.
   - [ ] Implement limiter enforcement and structured 429 responses with request IDs.
   - [ ] Surface aggregate counters in admin dashboards/telemetry.
   - [ ] Add unit/integration tests and operator documentation.

**B. Existing markdown/docs to update**

1. **README.md** — switch FastAPI/FAISS/Eleventy → Next.js/pgvector/Prisma/Auth.js; include Windows-friendly commands & `.env` examples.
   - [ ] Audit outdated stack references and screenshots.
   - [ ] Rewrite quick start/runbooks for Next.js + pgvector flow (Windows + macOS/Linux).
   - [ ] Cross-link updated docs (AGENTS, OPERATIONS, SECURITY) and confirm hero messaging.
2. **ARCHITECTURE.md** — diagrams for pgvector flows + SSE; remove Jinja/Nunjucks.
   - [ ] Update architecture diagrams/sequence charts for Next.js + Postgres topology.
   - [ ] Replace narrative references to FAISS/FastAPI with pgvector/Auth.js stack details.
   - [ ] Document SSE streaming contract and planned re-ranker integration.
3. **OPERATIONS.md** — DB backup/restore; RLS policy examples; pgvector DDL and `probes` docs.
   - [ ] Add pgvector install/maintenance guidance and backup/restore runbooks.
   - [ ] Document RLS policy management, IAM/secret rotation, and escalation SOPs.
   - [ ] Reconcile CLI commands/make targets with new workflow.
4. **TROUBLESHOOTING.md** — Auth.js email flow; pgvector extension issues; Prisma migration conflicts; SSE timeouts.
   - [ ] Capture Auth.js email magic link failure scenarios and fixes.
   - [ ] Add pgvector + Prisma troubleshooting (extension enablement, migration drift).
   - [ ] Note SSE timeout/root-cause patterns and mitigation steps.
5. **REQUIREMENTS.md** — add Postgres + Prisma; deprecate FAISS/Jinja2; keep Windows notes.
   - [ ] Update functional/non-functional requirements to highlight new stack.
   - [ ] Remove deprecated components and clarify migration timeline.
   - [ ] Ensure Windows contributors have clear setup/testing guidance.

**C. Items to carry into AGENTS (non-conflicting)**

1. **CI gates** — keep lint/test/eval/release; adjust for TS/Next.js later; preserve eval gate.
   - [ ] Align GitHub Actions matrix with Next.js + Postgres requirements.
   - [ ] Verify local `make quality` mirrors CI steps and coverage thresholds.
   - [ ] Document PR gating expectations inside AGENTS and CONTRIBUTING.
2. **Dictionary/glossary admin** — keep concept; migrate storage to DB; surface in Admin.
   - [ ] Design Prisma schema/API contracts for glossary records with approval workflow.
   - [ ] Implement admin UI for propose/review/approve flows with RBAC checks.
   - [ ] Seed baseline glossary entries and add documentation/tests.

**D. Documentation depth improvements**

1. **Glossary** admin page spec + DB schema with reviewer propose → admin approve flow.
   - [ ] Draft UX flow, permissions, and data model diagrams.
   - [ ] Share spec for review and iterate with stakeholders.
   - [ ] Convert approved spec into implementation tickets/tasks.
2. **Sample Seed** corpus (CED) + `make seed` target.
   - [ ] Curate minimal CED documents and sanitize for distribution.
   - [ ] Build automated seeding script/Make target populating DB + storage.
   - [ ] Add verification tests and contributor docs.
3. **reports/** with retrieval eval CSV + small HTML summary; publish in CI.
   - [ ] Define report schema (metrics, charts) for evaluation runs.
   - [ ] Update evaluation pipeline to emit CSV/HTML artifacts.
   - [ ] Configure CI to upload artifacts and document consumption workflow.

**E. File-specific TODOs from audit**

1. `atticus/config.py` — remove `faiss_index_path`/file-index fields; add `DATABASE_URL`, `EMBEDDING_DIM`, vector tunables (lists/probes).
   - [ ] Delete FAISS-specific fields and defaults.
   - [ ] Introduce Postgres/vector configuration with validation and docs.
   - [ ] Update tests/utilities relying on old settings.
2. `atticus/faiss_index.py` — delete; replace with pgvector DAO (CRUD for `documents/chunks`, cosine search).
   - [ ] Port shared dataclasses/helpers needed by new DAO.
   - [ ] Implement pgvector repository with cosine similarity queries.
   - [ ] Remove FAISS module references throughout repo.
3. `api/main.py` — drop Jinja2 templates/static mounts; stop serving `/` HTML; keep JSON APIs; Next.js owns UI.
   - [ ] Remove template/static configuration and unused imports.
   - [ ] Confirm API router mounts only expose JSON endpoints.
   - [ ] Update deployment docs referencing FastAPI-served UI.
4. `api/routes/chat.py` and `api/routes/ask.py` — consolidate; ensure `request_id` & `should_escalate`; remove unused import in `api/routes/__init__.py`.
   - [ ] Merge route handlers and delete deprecated module.
   - [ ] Guarantee response includes `request_id`/`should_escalate` and shared error handling.
   - [ ] Clean up router exports/imports and associated tests.
5. `Makefile` — remove `ui` target (`http.server`); add Next.js scripts (`dev`, `build`, `start`); keep `api` until migration complete.
   - [ ] Drop legacy `ui` implementation and confirm new targets wrap Next.js commands.
   - [ ] Ensure CI/README references use updated make targets.
   - [ ] Re-run `make help`/docs to validate instructions.
6. `requirements.in` — remove `faiss-cpu`, `jinja2`; add `psycopg[binary]` for local Python dev until TS/Next.js replaces Python API.
   - [ ] Prune deprecated dependencies and add Postgres driver entry.
   - [ ] Regenerate `requirements.txt`/lockfiles and verify tests pass.
   - [ ] Update docs referencing dependency installation.
7. `ARCHITECTURE.md` & legacy `AGENTS.md` — replace FAISS/FastAPI mentions with references to this doc; mark migration phases.
   - [ ] Identify all legacy references and map to new terminology.
   - [ ] Rewrite sections to align with Next.js/pgvector plan and note migration status.
   - [ ] Link back to authoritative AGENTS/TODO entries.

## Uncategorized


## Product & Audience

*(No active items.)*

## Retrieval

*(No active items.)*

## API & UI


## Tooling

*(No active items.)*

## Documentation

---

> Keep this list accurate and up to date. Once a task is finished, move it to [ToDo-Complete.md](ToDo-Complete.md) with the completion date and relevant commit ID.
