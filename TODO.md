# TODO — Atticus (Consolidated Outstanding Items)

This file replaces previous scattered TODOs and audit todos. It tracks only what is **still relevant**.

## 1) Glossary Seed & Runbook
**Goal:** deterministic baseline data + clear reset/rollback steps.

**Deliverables**
- Extend `prisma/seed.ts` with sample entries covering states: `approved`, `pending`, `rejected` (stable IDs).
- Add pytest `tests/test_seed_manifest.py` asserting baseline rows exist after `make db.seed`.
- Update docs:
  - `OPERATIONS.md` — how to reset/rollback glossary.
  - `docs/glossary-spec.md` — provisioning + rollback guidance.

**Acceptance**
- `make db.seed` produces deterministic rows; tests pass; docs explain reset/rollback for each environment.

---

## 2) Glossary UX Follow-through
**Goal:** visualise the review/approve path and capture decisions.

**Deliverables**
- Add Mermaid sequence diagram to `docs/glossary-spec.md`:
  ```mermaid
  sequenceDiagram
    participant Reviewer
    participant Admin
    Reviewer->>Admin: Submit glossary entry
    Admin->>System: Approve/Reject
    System-->>Reviewer: Status update + audit log
  ```
- Append ADR links or short “Decision Notes” explaining why this workflow was chosen.

**Acceptance**
- Spec renders with diagram + decisions; open follow-ups (notifications, audit UI) listed as backlog links.

---

## 3) RBAC Integration Coverage
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

## 4) pgvector GUC Bootstrap
**Goal:** fresh DBs pass `make db.verify` without manual steps.

**Deliverables**
- Migration that ensures `set_config('app.pgvector_lists','100', true)` is present (idempotent).
- (Optional) Enhance `scripts/db_verify.py` to assert the GUC exists and print effective value.
- Update `OPERATIONS.md` with rollback/override notes.

**Acceptance**
- New environments pass `make db.verify`; docs show how to override the value.

---

## 5) Version Parity Automation
**Goal:** prevent drift between `VERSION`, `package.json`, and API metadata.

**Deliverables**
- Script `scripts/check_version_parity.py` to compare `VERSION` ↔ `package.json.version`.
- Makefile target `version-check`; include in `quality` (and optionally `verify`).
- Brief note in `README.md` / `RELEASE.md` about keeping versions in lockstep.

**Acceptance**
- CI fails when versions drift; local `make quality` surfaces mismatch immediately.

