# TODO_NEW — Atticus Outstanding Work

This document consolidates the remaining remediation work captured across the audit
artifacts. Each item lists the required deliverables, implementation steps, and
acceptance criteria so ownership can be assigned quickly.

## 1. Glossary baseline & documentation hardening
- **Goal:** Deliver a production-ready glossary workflow with deterministic seed data and
  contributor guidance.
- **Scope:**
  - Extend `prisma/seed.ts` (and related Make targets) to insert a small set of
    representative glossary entries covering approved, pending, and rejected states.
  - Add Vitest/pytest coverage that exercises glossary reads after `make seed` to guard
    against regressions.
  - Update contributor docs (README, OPERATIONS, TROUBLESHOOTING, `docs/glossary-spec.md`)
    with provisioning, rollback, and tenant-scoped seeding steps.
- **Dependencies:** Requires an updated Prisma migration if new enum values or fields are
  introduced. Coordinate with DBA to ensure seed data is idempotent across environments.
- **Acceptance criteria:** `make seed` populates glossary rows deterministically, tests
  assert baseline availability, and runbooks document how to reset or roll back glossary
  data for each environment.

## 2. Glossary UX specification follow-through
- **Goal:** Close the loop on the glossary admin design work captured in the current spec.
- **Scope:**
  - Produce lightweight sequence diagrams (PlantUML or Mermaid) illustrating reviewer →
    admin approval flows and embed them in `docs/glossary-spec.md`.
  - Capture review feedback/resolution in the spec (link to decisions or ADRs) so future
    contributors understand why the current workflow was chosen.
  - Break remaining implementation follow-ups (e.g., notifications, audit logging UI) into
    backlog tickets linked from this document.
- **Dependencies:** Depends on the baseline glossary seed (Item 1) so reviewers can validate
  flows with real data.
- **Acceptance criteria:** `docs/glossary-spec.md` includes diagrams, decision records, and
  a checklist of spun-off tickets with owners/status.

## 3. Cross-stack RBAC integration coverage
- **Goal:** Prove that RBAC restrictions hold across both FastAPI and Next.js layers.
- **Scope:**
  - Add Playwright coverage for reviewer sessions interacting with `/admin` and `/api/glossary`
    endpoints, asserting redirects/403s for non-admin roles and successful CRUD for admins.
  - Introduce API-level tests (Vitest or Next.js route unit tests) that simulate requests to
    `app/api/glossary` handlers using mocked sessions for each role.
  - Extend pytest coverage for FastAPI legacy `/admin/dictionary` endpoints to ensure
    unauthorized tokens still receive contract-compliant 401/403 payloads.
- **Dependencies:** Requires stable test fixtures for Auth.js sessions and FastAPI admin
  tokens. Coordinate with CI to ensure Playwright secrets are available.
- **Acceptance criteria:** New tests fail if RBAC protections regress; CI surfaces them under
  `make quality` and the GitHub Actions frontend job.

## 4. pgvector configuration bootstrap
- **Goal:** Eliminate manual steps when configuring `app.pgvector_lists` so `make db.verify`
  is reliable in fresh environments.
- **Scope:**
  - Add a Prisma migration or SQL bootstrap script that sets `app.pgvector_lists` using
    `ALTER SYSTEM` or database-level `set_config` for the target database.
  - Document the change in OPERATIONS/TROUBLESHOOTING with rollback instructions and
    environment-specific overrides.
  - Update `scripts/verify_pgvector.sql` (and tests) to assert the bootstrap ran before
    proceeding.
- **Dependencies:** Coordinate with DBA/SRE to ensure configuration changes comply with
  managed Postgres constraints.
- **Acceptance criteria:** Fresh databases pass `make db.verify` without manual `SET
  app.pgvector_lists`, documentation reflects the automation, and CI captures the new guard.

## 5. Version parity automation
- **Goal:** Prevent drift between `VERSION`, `package.json`, and FastAPI metadata.
- **Scope:**
  - Add a lightweight script or unit test that compares the values at build/test time,
    failing if they diverge.
  - Wire the check into `make quality` and CI workflows.
  - Document the workflow (README + RELEASE.md) so release engineers know how to update
    version numbers safely.
- **Dependencies:** Requires access to both Node and Python environments during the check;
  consider implementing in Python for portability.
- **Acceptance criteria:** CI fails when any version source drifts, and documentation outlines
  the single source of truth along with update instructions.
