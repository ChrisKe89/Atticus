# TODO - Atticus (Authoritative Active List)

This file is the **single source of truth** for active tasks.
Items completed are moved to [ToDo-Complete.md](ToDo-Complete.md).

**A. Existing markdown/docs to update**

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

**B. Items to carry into AGENTS (non-conflicting)**

1. **CI gates** — keep lint/test/eval/release; adjust for TS/Next.js later; preserve eval gate.
   - [ ] Align GitHub Actions matrix with Next.js + Postgres requirements.
   - [ ] Verify local `make quality` mirrors CI steps and coverage thresholds.
   - [ ] Document PR gating expectations inside AGENTS and CONTRIBUTING.
2. **Dictionary/glossary admin** — keep concept; migrate storage to DB; surface in Admin.
   - [ ] Design Prisma schema/API contracts for glossary records with approval workflow.
   - [ ] Implement admin UI for propose/review/approve flows with RBAC checks.
   - [ ] Seed baseline glossary entries and add documentation/tests.

**C. Documentation depth improvements**

1. **Glossary** admin page spec + DB schema with reviewer propose → admin approve flow.
   - [ ] Draft UX flow, permissions, and data model diagrams.
   - [ ] Share spec for review and iterate with stakeholders.
   - [ ] Convert approved spec into implementation tickets/tasks.

**D. File-specific TODOs from audit**

1. `api/main.py` — drop Jinja2 templates/static mounts; stop serving `/` HTML; keep JSON APIs; Next.js owns UI.
   - [ ] Remove template/static configuration and unused imports.
   - [ ] Confirm API router mounts only expose JSON endpoints.
   - [ ] Update deployment docs referencing FastAPI-served UI.
2. `api/routes/chat.py` and `api/routes/ask.py` — consolidate; ensure `request_id` & `should_escalate`; remove unused import in `api/routes/__init__.py`.
   - [ ] Merge route handlers and delete deprecated module.
   - [ ] Guarantee response includes `request_id`/`should_escalate` and shared error handling.
   - [ ] Clean up router exports/imports and associated tests.
3. `Makefile` — remove `ui` target (`http.server`); add Next.js scripts (`dev`, `build`, `start`); keep `api` until migration complete.
   - [ ] Drop legacy `ui` implementation and confirm new targets wrap Next.js commands.
   - [ ] Ensure CI/README references use updated make targets.
   - [ ] Re-run `make help`/docs to validate instructions.
4. `requirements.in` — remove `faiss-cpu`, `jinja2`; add `psycopg[binary]` for local Python dev until TS/Next.js replaces Python API.
   - [ ] Prune deprecated dependencies and add Postgres driver entry.
   - [ ] Regenerate `requirements.txt`/lockfiles and verify tests pass.
   - [ ] Update docs referencing dependency installation.
5. `ARCHITECTURE.md` & legacy `AGENTS.md` — replace FAISS/FastAPI mentions with references to this doc; mark migration phases.
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
