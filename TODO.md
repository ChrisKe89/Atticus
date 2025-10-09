# TODO — Atticus

This file replaces previous scattered TODOs and audit todos. It tracks only what is **still relevant**.

## 1) pgvector GUC Bootstrap
**Goal:** fresh DBs pass `make db.verify` without manual steps.

**Deliverables**
- Migration that ensures `set_config('app.pgvector_lists','100', true)` is present (idempotent).
- (Optional) Enhance `scripts/db_verify.py` to assert the GUC exists and print effective value.
- Update `OPERATIONS.md` with rollback/override notes.

**Acceptance**
- New environments pass `make db.verify`; docs show how to override the value.

---

## 2) Version Parity Automation
**Goal:** prevent drift between `VERSION`, `package.json`, and API metadata.

**Deliverables**
- Script `scripts/check_version_parity.py` to compare `VERSION` ↔ `package.json.version`.
- Makefile target `version-check`; include in `quality` (and optionally `verify`).
- Brief note in `README.md` / `RELEASE.md` about keeping versions in lockstep.

**Acceptance**
- CI fails when versions drift; local `make quality` surfaces mismatch immediately.

---

## 3) Uncertain Chat Validation Flow
**Goal:** make the “low confidence” path observable and correctable.

**Deliverables**
- Backend: whenever an answer is produced with `confidence < CONFIDENCE_THRESHOLD`, set `chats.status='pending_review'` and persist `{question, top_k sources, request_id}`.
- Route: `POST /api/admin/uncertain/:id/ask-followup` → stores a canonical follow-up prompt on the chat.
- UI: review drawer shows full context (question, answer, sources, request_id); buttons call the routes above.
- Tests: Playwright spec that (1) creates a low-confidence chat fixture, (2) sees it in Uncertain, (3) approves it, and (4) confirms status flips to `reviewed`.

**Acceptance**
- A low-confidence chat appears in Uncertain within one run; actions change status and are reflected in DB + UI; tests green.

## 4) Dictionary (Glossary) Update Semantics
**Goal:** safe, idempotent updates to existing terms; create on first write.

**Deliverables**
- API: `PUT /api/glossary/:id` (update by id) and `POST /api/glossary` (create); both require `admin`, fall back to **upsert** on unique `(org_id, term)`.
- Validation: reject empty `term`/`definition`; normalise whitespace; optional `synonyms[]`.
- Auditing: write to `rag_events` (actor, action, glossary_id, before/after).
- UI: inline edit row → optimistic update; toast on success/failure.

**Acceptance**
- Updating an existing term changes it in place (no duplicates); creating a non-existent term inserts it; RBAC enforced; audit row written.
