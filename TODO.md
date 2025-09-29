# TODO - Atticus (Authoritative Active List)

This file is the **single source of truth** for active tasks.
Items completed are moved to [ToDo-Complete.md](ToDo-Complete.md).

**A. Existing markdown/docs to update**

_(All Section A documentation tasks completed 2025-09-28 — see ToDo-Complete.md for details.)_

**B. Items to carry into AGENTS (non-conflicting)**

_(Section B.1 CI gates addressed 2025-09-28 — see ToDo-Complete.md.)_ 2. **Dictionary/glossary admin** — keep concept; migrate storage to DB; surface in Admin.

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
2. `ARCHITECTURE.md` & legacy `AGENTS.md` — replace FAISS/FastAPI mentions with references to this doc; mark migration phases.
   - [ ] Identify all legacy references and map to new terminology.
   - [ ] Rewrite sections to align with Next.js/pgvector plan and note migration status.
   - [ ] Link back to authoritative AGENTS/TODO entries.

## Uncategorized

## Product & Audience

_(No active items.)_

## Retrieval

_(No active items.)_

## API & UI

## Tooling

_(No active items.)_

## Documentation

---

> Keep this list accurate and up to date. Once a task is finished, move it to [ToDo-Complete.md](ToDo-Complete.md) with the completion date and relevant commit ID.
