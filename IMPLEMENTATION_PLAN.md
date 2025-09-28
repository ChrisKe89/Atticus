# Implementation Plan — Atticus RAG Consistency Cleanup

This plan sequences remediation work uncovered in `AUDIT_REPORT.md` and merges active TODOs. Each phase lists required commits, commands (POSIX + PowerShell where relevant), acceptance criteria, and cross-references to TODO items.

## Phase 0 – Safety, Branching, and Baseline Artifacts
- **Objectives**
  - Create working branch `audit/rag-consistency-cleanup`.
  - Ensure `.env.example` covers all required settings before touching secrets (extends TODO §A.1).
  - Capture dependency baselines and enable new audit scripts.
- **Commits**
  - `chore(phase-0): scaffold audit automation and env template`
- **Key Tasks**
  - Copy `.env.example` → `.env` locally; verify `scripts/generate_env.py` parity.
  - Run `npm install`, `pip-sync requirements.txt` (POSIX) / `python -m pip install -r requirements.txt` (PowerShell) to capture lockfile state.
  - Document any failing installs in TROUBLESHOOTING.md (links to TODO §A.4).
- **Commands**
  - POSIX: `git checkout -b audit/rag-consistency-cleanup`
  - PowerShell: `git checkout -b audit/rag-consistency-cleanup`
- **Acceptance Criteria**
  - Branch created, `.env` generated without manual edits.
  - Audit scripts executable (`npm run audit:ts`, `python scripts/audit_unused.py`).

## Phase 1 – Data Layer First (TODO §A.3, §A.4, §D.4)
- **Objectives**
  - Model pgvector schema via Prisma; align Python + Prisma migrations.
  - Add `scripts/verify_pgvector.sql` checks to CI + docs.
- **Commits**
  - `feat(phase-1): align prisma schema with pgvector tables`
  - `chore(phase-1): add pgvector verification script and docs`
- **Key Tasks**
  - Extend `prisma/schema.prisma` with vector tables/indexes (`atticus_chunks`, `atticus_documents`).
  - Create migration enabling `CREATE EXTENSION vector`, IVFFlat index, and default probes (ties to TODO §A.3 and FND-006).
  - Update `requirements.in`/`pyproject.toml` notes around `psycopg[binary]` (TODO §D.4).
  - Wire verification SQL into Makefile + CI.
- **Commands**
  - POSIX: `npm run db:migrate`, `psql $DATABASE_URL -f scripts/verify_pgvector.sql`
  - PowerShell: `psql $env:DATABASE_URL -f scripts/verify_pgvector.sql`
- **Acceptance Criteria**
  - Prisma migration applies cleanly on empty DB and existing dev DB.
  - `scripts/verify_pgvector.sql` returns success; Make/CI step added.

## Phase 2 – RAG Contract Unification (TODO §D.2)
- **Objectives**
  - Provide single `/api/ask` endpoint returning `{answer, sources, confidence, request_id, should_escalate}`.
  - Introduce shared DTOs for TypeScript + Python, with typed fetch layer.
- **Commits**
  - `feat(phase-2): unify ask contract across api and app`
  - `test(phase-2): cover ask contract from Next app`
- **Key Tasks**
  - Implement `app/api/ask/route.ts` or proxy to FastAPI with SSE support.
  - Refactor `api/routes/chat.py` to share dataclasses/validators; ensure same schema.
  - Update Next chat surface to call API, handle streaming, log `request_id` (FND-003/FND-007).
  - Add Vitest + pytest coverage verifying contract.
- **Commands**
  - POSIX: `npm run test:unit`, `pytest tests/test_chat_route.py`
  - PowerShell: `npm run test:unit`, `pytest tests/test_chat_route.py`
- **Acceptance Criteria**
  - Contract identical in TypeScript types and Pydantic schema.
  - Chat UI renders streaming responses with sources + error handling.

## Phase 3 – Auth & RBAC Hardening (TODO §B.2, §C.1)
- **Objectives**
  - Finalize Prisma schema for glossary workflow, enforce RBAC across server actions.
  - Document provisioning, tests, and rollback steps.
- **Commits**
  - `feat(phase-3): harden glossary admin workflows`
  - `docs(phase-3): update auth runbooks`
- **Key Tasks**
  - Finish Glossary admin propose/review/approve flow (TODO §B.2, §C.1).
  - Add middleware tests ensuring non-admins blocked (Next + FastAPI).
  - Update TROUBLESHOOTING.md with Auth.js issues (TODO §A.4).
- **Commands**
  - POSIX: `npm run test:e2e`, `pytest tests/test_admin_route.py`
  - PowerShell: `npm run test:e2e`, `pytest tests/test_admin_route.py`
- **Acceptance Criteria**
  - Admin panel fully functional, RBAC enforced server-side.
  - Docs include Windows-friendly auth smoke steps.

## Phase 4 – Frontend Hygiene (TODO §A.1, FND-001/002/007)
- **Objectives**
  - Align Tailwind content paths, remove unused animations, integrate Framer Motion intentionally or remove.
  - Normalize shadcn/ui component usage, ensure Lucide imports tree-shaken.
- **Commits**
  - `refactor(phase-4): consolidate ui components`
  - `style(phase-4): prune legacy tailwind artefacts`
- **Key Tasks**
  - Remove `web/static` (archive if needed) and migrate interactions into Next pages.
  - Adopt shadcn/ui primitives for form controls and table (Glossary panel).
  - Add Framer Motion variants if keeping dependency; otherwise drop.
  - Update Tailwind config to cover new paths (e.g., `lib`, `content`, `docs` if needed).
- **Commands**
  - POSIX: `npm run lint`, `npm run build`
  - PowerShell: `npm run lint`, `npm run build`
- **Acceptance Criteria**
  - `npm run audit:ts` passes with no unused components.
  - Tailwind build has no purge misses; UI uses consistent design tokens.

## Phase 5 – Orphans & Structure Cleanup (TODO §D.1, §D.3)
- **Objectives**
  - Remove FastAPI UI vestiges, restructure repo to separate frontend/back-end clearly.
- **Commits**
  - `refactor(phase-5): remove fastapi ui remnants`
  - `docs(phase-5): align architecture diagrams`
- **Key Tasks**
  - Update `ARCHITECTURE.md` diagrams and AGENTS with new structure (TODO §A.2, §D.5).
  - Drop `api/routes/chat.py` duplication once Next handles ask flow, or vice versa per decision.
  - Update Make targets removing `ui` alias to `npm run dev` once Next is canonical.
- **Commands**
  - POSIX: `make help`
  - PowerShell: `make help`
- **Acceptance Criteria**
  - No orphaned routes/components flagged by `npm run audit:ts` or `python scripts/audit_unused.py`.
  - Repo tree matches updated `REPO_STRUCTURE.md`.

## Phase 6 – Developer Experience & CI (TODO §B.1)
- **Objectives**
  - Harmonize linting/formatting (ESLint, Prettier, Ruff, Black, mypy) and ensure CI runs frontend + backend gates.
- **Commits**
  - `chore(phase-6): extend ci matrix for web stack`
  - `chore(phase-6): tighten lint/typecheck configs`
- **Key Tasks**
  - Add ESLint config for shadcn/ui, enable Prettier/biome or confirm formatting strategy.
  - Update GitHub Actions to run `npm run lint`, `npm run typecheck`, `npm run build` on Node 20 matrix with Postgres service.
  - Integrate audit scripts into CI (knip, route audit, vulture) and surface reports as artifacts.
  - Address `npm audit` vulnerabilities or document exceptions.
- **Commands**
  - POSIX: `npm run lint`, `npm run typecheck`, `npm run build`, `python -m pytest`
  - PowerShell: same commands.
- **Acceptance Criteria**
  - CI green with combined Node + Python jobs.
  - Pre-commit hooks cover Ruff, mypy, ESLint, Prettier.

## Phase 7 – Documentation Sync & Release (TODO §A.1–§A.5, §B.1)
- **Objectives**
  - Rewrite README/ARCHITECTURE/OPERATIONS/TROUBLESHOOTING/REQUIREMENTS to match final stack.
  - Update AGENTS.md with resolved conflicts, escalate instructions, and CI gates.
  - Publish release notes & upgrade guidance per semantic version policy.
- **Commits**
  - `docs(phase-7): refresh product documentation`
  - `release(phase-7): bump version and changelog`
- **Key Tasks**
  - Complete TODO items under sections A–C in TODO.md; move finished tasks to `ToDo-Complete.md`.
  - Add upgrade/rollback steps to README + RELEASE.md (per universal backlog instructions).
  - Provide Windows PowerShell equivalents for all scripts/make invocations.
- **Commands**
  - POSIX: `git tag vX.Y.Z`
  - PowerShell: `git tag vX.Y.Z`
- **Acceptance Criteria**
  - `TODO.md` reflects only new/remaining work; duplicates removed.
  - `CHANGELOG.md` documents release with version synced across packages.
  - README accurately describes Next.js + FastAPI hybrid deployment.

## Cross-Phase Considerations
- **Observability**: Introduce metrics dashboards/log shipping in Phases 2–3 when RAG contract and auth are stable.
- **Testing**: Maintain ≥90% backend coverage and add Vitest/Playwright coverage >80% for UI flows.
- **Versioning**: Adopt single `VERSION` file updated in Phase 7; reference from Python/Node builds.
- **Risk Mitigation**: For destructive deletions (e.g., `web/static`), move to `archive/legacy-ui/` first, update documentation, and remove once parity confirmed.

