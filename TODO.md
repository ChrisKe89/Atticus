# TODO — Atticus

This file replaces previous scattered TODOs and audit todos. It tracks only what is **still relevant**.

## 1) RBAC Integration Coverage
**Goal:** prove role gates across **Next.js** and **FastAPI**.

**Deliverables**
- **Playwright** specs:
  - Non-admin → `/admin` and `/api/glossary` → `403/redirect`.
  - Admin can CRUD glossary.
- **API/route tests**:
  - Next route handlers with mocked sessions for each role.
  - FastAPI admin endpoints with invalid/missing admin token return `401/403` contracts.

**Acceptance**
- Tests fail on regressions; wired into CI via `make quality` / frontend job.

---

## 2) pgvector GUC Bootstrap
**Goal:** fresh DBs pass `make db.verify` without manual steps.

**Deliverables**
- Migration that ensures `set_config('app.pgvector_lists','100', true)` is present (idempotent).
- (Optional) Enhance `scripts/db_verify.py` to assert the GUC exists and print effective value.
- Update `OPERATIONS.md` with rollback/override notes.

**Acceptance**
- New environments pass `make db.verify`; docs show how to override the value.

---

## 3) Version Parity Automation
**Goal:** prevent drift between `VERSION`, `package.json`, and API metadata.

**Deliverables**
- Script `scripts/check_version_parity.py` to compare `VERSION` ↔ `package.json.version`.
- Makefile target `version-check`; include in `quality` (and optionally `verify`).
- Brief note in `README.md` / `RELEASE.md` about keeping versions in lockstep.

**Acceptance**
- CI fails when versions drift; local `make quality` surfaces mismatch immediately.

---

## 4) Admin Ops Console (Uncertain Chats, Tickets, Glossary)
**Goal:** give reviewers a single place to triage low-confidence chats, manage tickets, and edit glossary.

**Deliverables**
- **UI**: `/admin` with tabs — **Uncertain**, **Tickets**, **Glossary**.
  - Uncertain: table (date, user, question, confidence, top sources) + actions (**Approve**, **Ask Follow-up**, **Escalate**).
  - Tickets: list AExxx with status, assignee, last activity.
  - Glossary: search + inline edit (RBAC-gated).
- **API**:
  - `GET /api/admin/uncertain` — list chats where `confidence < CONFIDENCE_THRESHOLD` and `status='pending_review'`.
  - `POST /api/admin/uncertain/:id/approve` — marks reviewed; persists reviewer + timestamp.
  - `POST /api/admin/uncertain/:id/escalate` — creates/links AE ticket, logs action.
- **DB** (Prisma):
  - `chats`: add columns `confidence FLOAT`, `status TEXT DEFAULT 'ok'`, `reviewed_by`, `reviewed_at`.
  - `tickets`: ensure `AE` id, `status`, `assignee`, `linked_chat_id`.
- **RBAC**: only `admin` sees `/admin`; `reviewer` sees Uncertain+Glossary read, limited write.

**Acceptance**
- `reviewer` cannot access admin-only actions; `admin` can.
- Uncertain list populates from real chats; actions emit audit events; Playwright + API tests cover 403s for non-admins.

---

## 5) Uncertain Chat Validation Flow
**Goal:** make the “low confidence” path observable and correctable.

**Deliverables**
- Backend: whenever an answer is produced with `confidence < CONFIDENCE_THRESHOLD`, set `chats.status='pending_review'` and persist `{question, top_k sources, request_id}`.
- Route: `POST /api/admin/uncertain/:id/ask-followup` → stores a canonical follow-up prompt on the chat.
- UI: review drawer shows full context (question, answer, sources, request_id); buttons call the routes above.
- Tests: Playwright spec that (1) creates a low-confidence chat fixture, (2) sees it in Uncertain, (3) approves it, and (4) confirms status flips to `reviewed`.

**Acceptance**
- A low-confidence chat appears in Uncertain within one run; actions change status and are reflected in DB + UI; tests green.

---

## 6) Dictionary (Glossary) Update Semantics
**Goal:** safe, idempotent updates to existing terms; create on first write.

**Deliverables**
- API: `PUT /api/glossary/:id` (update by id) and `POST /api/glossary` (create); both require `admin`, fall back to **upsert** on unique `(org_id, term)`.
- Validation: reject empty `term`/`definition`; normalise whitespace; optional `synonyms[]`.
- Auditing: write to `rag_events` (actor, action, glossary_id, before/after).
- UI: inline edit row → optimistic update; toast on success/failure.

**Acceptance**
- Updating an existing term changes it in place (no duplicates); creating a non-existent term inserts it; RBAC enforced; audit row written.
