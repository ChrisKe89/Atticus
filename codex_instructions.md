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
