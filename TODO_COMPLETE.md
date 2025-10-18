
# TODO — Completed / Obsolete

This file is the **permanent log of completed tasks**.
Each entry includes the completion date and commit reference for traceability.

The following items are done or no longer relevant and are recorded here for traceability.

## Completed
- **FND-001 → FND-008** (Audit): Next.js UI, proxy contracts, schema ownership, env scaffolding, request-id propagation, CI audits — delivered.
- **Ask Contract & Streaming**: `/api/ask` SSE endpoint and UI consumer normalised; error contracts include `request_id`.
- **Frontend Hygiene & Repo Structure**: Legacy FastAPI UI archived; canonical Next.js app; docs updated.
- **DX & Docs**: Makefile `quality` runs Python + Next gates + audits; pre-commit configured; release docs added.
- **Structured Logging**: Centralised logger with JSON output; instrumented key scripts.
- **Unified CLI**: `scripts/atticus_cli.py` with Makefile alias `atticus`.

## Obsolete / Superseded
- “Prisma duplicates and `Glossary.synonyms` type fix” — resolved in current schema/migrations.
- “Decide on Framer Motion” — kept as optional; AGENTS reflects this.
- “Archive web/static” — done; legacy moved under `archive/legacy-ui/`.
- “CONTENT_DIR → CONTENT_ROOT rename” — standardised across code/docs.
- “Rebuild evaluator harness” — present via tests and `eval` target.
- “Glossary API error normalisation” — implemented with `request_id`.

---

## 2025-11-03

- [x] TODO "Prompt/Eval Governance" — introduced versioned prompt template registry with configurable `GEN_PROMPT_VERSION`, pinned evaluation thresholds via `EVAL_MIN_NDCG`/`EVAL_MIN_MRR`, enforced gating in `scripts/eval_run.py`, updated docs/env scaffolding, and added regression tests — completed 2025-11-03 (this change set).

---

## 2025-11-02

- [x] TODO "Hybrid Retrieval" — added explicit retrieval modes (hybrid, vector, lexical), multi-mode evaluation outputs (`retrieval_modes.json`), configuration toggles, documentation updates, and regression tests to track BM25 + vector fusion metrics end to end — completed 2025-11-02 (this change set).

---

## 2025-10-31

- [x] Admin Page Extensions — delivered ingestion panel, glossary viewer, and eval seed manager in the standalone admin console with secured FastAPI endpoints, tests, docs, and configuration updates — completed 2025-10-31 (this change set).

---

## 2025-10-18

- [x] Delivered the multi-model query splitter (AI / RAG Enhancements) with targeted prompts, chat integration, documentation, tests, and version bump — completed 2025-10-18 (this change set).
- [x] TODO "Feedback Loop" — implemented the end-to-end capture, seed document generation, admin triage workflows, documentation, and regression tests for the new feedback loop — completed 2025-10-18 (this change set).

---

## 2025-10-10

- [x] Added model parser/resolver unit tests, retrieval filter coverage, API clarification regressions, UI integration tests, and a gated Playwright chat clarification flow — completed 2025-10-10 (this change set).
- [x] Documented model disambiguation behaviour in `AGENTS.md`, `README.md`, and `docs/ATTICUS_DETAILED_GUIDE.md`; updated `CHANGELOG.md`, and reconciled TODO status — completed 2025-10-10 (this change set).
- [x] Verified direct/unclear/multi-model acceptance criteria via automated tests and ensured `make quality` (lint, typecheck, pytest, Next build, ts audit) passes end-to-end — completed 2025-10-10 (this change set).

---

## 2025-09-21

- [x] Provided `.env.example` for local configuration scaffolding — completed 2025-09-21 (commit 5df0d73).
- [x] Delivered Dockerized stack (API/Nginx Dockerfiles, docker-compose workflow, healthchecks, Makefile targets) — completed 2025-09-21 (commit 5df0d73).
- [x] Published hardened `nginx.conf` for TLS termination and proxying to the FastAPI service — completed 2025-09-21 (commit 5df0d73).
- [x] Established single-node, containerized stack with minimal dependencies — completed 2025-09-21 (commit 3013a1a).
- [x] Removed Azure AD/SSO code paths and noted migration in README — completed 2025-09-21 (commit 3013a1a).
- [x] Pinned OpenAI defaults to `text-embedding-3-large` and `gpt-4.1` — completed 2025-09-21 (commit 3013a1a).
- [x] Created base repository structure (`atticus/`, `api/`, `ingest/`, etc.) — completed 2025-09-21 (commit 3013a1a).
- [x] Added `.editorconfig`, `.gitattributes`, `.gitignore`, and `.vscode` settings — completed 2025-09-21 (commit 3013a1a).
- [x] Implemented pre-commit hooks with `ruff`, `mypy`, `markdownlint-cli2` — completed 2025-09-21 (commit 3013a1a).
- [x] Adopted `pip-tools` for locked dependencies — completed 2025-09-21 (commit 3013a1a).
- [x] Pinned core libraries (`fastapi`, `uvicorn`, `pydantic`, etc.) — completed 2025-09-21 (commit 3013a1a).
- [x] Built parsers for PDF, DOCX, XLSX, and HTML with OCR support — completed 2025-09-21 (commit 3013a1a).
- [x] Implemented evaluation harness with baseline metrics and gold set — completed 2025-09-21 (commit 3013a1a).

## 2025-09-23

- [x] Added environment generator (`scripts/generate_env.py`) with `--force` flag — completed 2025-09-23.
- [x] Implemented SMTP mailer (`atticus/notify/mailer.py`) using `.env` — completed 2025-09-23.
- [x] Created API `/contact` route for escalation email (202 Accepted) — completed 2025-09-23.
- [x] Built API `/ask` endpoint returning `{answer, sources, confidence}` — completed 2025-09-23.
- [x] Integrated modern UI served by FastAPI templates and static mounts — completed 2025-09-23.
- [x] Added `examples/dev.http` with sample `/ask` and `/contact` requests — completed 2025-09-23.

## 2025-09-25

- [x] Verified README/AGENTS/OPERATIONS cross-links and fixed relative paths - completed 2025-09-25 (commit 2a3b760).
- [x] Added SES IAM policy region lock guidance to SECURITY.md and reinforced README cross-link - completed 2025-09-25 (commit 2a3b760).
- [x] TODO "SECURITY.md — env-only secrets; SMTP `From` allow-list; RLS examples." - completed 2025-09-25 (commit 2a3b760).

- [x] Reviewed repository documentation set and normalised coverage messaging - completed 2025-09-25 (commit cd280f8).
- [x] Published secure remote access playbook (Tailscale, Cloudflare Tunnel, SSH) - completed 2025-09-25 (commit cd280f8).

## 2025-09-27

- [x] Implemented shared JSON error schema for API responses with request ID propagation tests — completed 2025-09-27 (commit 6dbf0b8).
- [x] TODO "Error JSON contract" - completed 2025-09-27 (commit 6dbf0b8).
- [x] Verified API-served UI via automated tests (pytest) and captured guidance in ATTICUS detailed guide - completed 2025-09-25 (commit cd280f8).
- [x] Enabled optional hybrid reranker with `ENABLE_RERANKER` flag and documented behaviour - completed 2025-09-25 (commit cd280f8).
- [x] Updated README hero copy to spotlight Sales/tender acceleration messaging - completed 2025-09-25 (commit cd280f8).
- [x] Documented `/ask` request/response schema in docs/api/README.md - completed 2025-09-25 (commit cd280f8).
- [x] Added `SMTP_DRY_RUN` mailer branch with tests and surfaced behaviour in docs - completed 2025-09-25 (commit cd280f8).
- [x] Made pytest parallelism conditional on pytest-xdist availability - completed 2025-09-25 (commit cd280f8).
- [x] Retired the legacy Jinja2/Eleventy UI in favour of a Tailwind-powered Next.js app covering chat, admin, settings, contact, and apps — completed 2025-09-27.

## 2025-09-28

- [x] TODO "Sample Seed corpus — Add verification tests and contributor docs." — completed 2025-09-28 (commit 19bdc5d).
- [x] TODO "reports/ — Update evaluation pipeline to emit CSV/HTML artifacts." — completed 2025-09-28 (commit 19bdc5d).
- [x] TODO "reports/ — Configure CI to upload artifacts and document consumption workflow." — completed 2025-09-28 (commit 19bdc5d).
- [x] TODO "README.md — rewrite for Next.js/pgvector stack with Windows guidance and quick start." — completed 2025-09-28 (commit 5c4ff5e).
- [x] TODO "ARCHITECTURE.md — update diagrams/narrative for Next.js + SSE flow." — completed 2025-09-28 (commit 5c4ff5e).
- [x] TODO "OPERATIONS.md — document pgvector maintenance, CI parity, and dependency risk handling." — completed 2025-09-28 (commit 5c4ff5e).
- [x] TODO "TROUBLESHOOTING.md — capture Auth.js email flow, SSE mitigation, lint/format guidance." — completed 2025-09-28 (commit 5c4ff5e).
- [x] TODO "REQUIREMENTS.md — align runtime/tooling requirements with Next.js + Prisma stack." — completed 2025-09-28 (commit 5c4ff5e).
- [x] TODO "CI gates — align GitHub Actions + local make quality" — completed 2025-09-28 (commit 5c4ff5e).
  > Continue logging future completed tasks below, grouped by date, to maintain a clear historical record.

## 2025-09-29

- [x] TODO "Tests: ingestion/retrieval unit + integration suite, regenerate requirements lock." — completed 2025-09-29 (commit 04216be).

## 2025-09-30

- [x] TODO "TROUBLESHOOTING.md — Add pgvector + Prisma troubleshooting (extension enablement, migration drift)." — completed 2025-09-30 (commit b7779b8).

## 2025-10-04

- [x] TODO "`Makefile` — remove `ui` target (`http.server`); add Next.js scripts (`dev`, `build`, `start`); keep `api` until migration complete." — completed 2025-10-04 (commit b7779b8).

- [x] TODO "`api/routes/chat.py` and `api/routes/ask.py` — consolidate; ensure request_id & should_escalate; remove unused import in api/routes/**init**.py." — completed 2025-10-04 (commit 2af9f6e).
- [x] TODO "Dictionary/glossary admin — Design Prisma schema/API contracts for glossary records with approval workflow." — completed 2025-10-04 (commit 2bc7206).
- [x] TODO "Dictionary/glossary admin — Implement admin UI for propose/review/approve flows with RBAC checks." — completed 2025-10-04 (commit 2bc7206).

## 2025-10-05

- [x] TODO "`api/main.py` — drop Jinja2 templates/static mounts; stop serving `/` HTML; keep JSON APIs; Next.js owns UI." — completed 2025-10-05 (present in commit 9a7620b9; verified during backlog audit).
- [x] TODO "`ARCHITECTURE.md` & legacy `AGENTS.md` — replace FAISS/FastAPI mentions with references to this doc; mark migration phases." — completed 2025-10-05 (present in commit 9a7620b9; verified during backlog audit).

## 2025-10-10

- [x] TODO "Glossary Seed & Runbook" — completed 2025-10-10 (this PR aligns Prisma seeds, docs, and verification tests).

## 2025-10-11

- [x] TODO "Glossary UX Follow-through" — completed 2025-10-11 (added workflow sequence diagram, decision notes, and backlog links in `docs/glossary-spec.md`).

## 2025-10-12

- [x] TODO "RBAC Integration Coverage" — completed 2025-10-12 (Playwright reviewer/admin coverage, Next.js route RBAC tests, FastAPI admin token assertions, and `make quality` wiring).

## 2025-10-14

- [x] TODO "Phase 5 — Orphans & Structure Cleanup" — completed 2025-10-14 (FastAPI now sources its version from `VERSION`, docs highlight Next.js as the canonical UI, and release notes capture the separation of backend and frontend responsibilities).

## 2025-10-15

- [x] TODO "Admin Ops Console (Uncertain Chats, Tickets, Glossary)" — completed 2025-10-15 (introduced Prisma chat/ticket models, Next.js admin tabs, RBAC-aware API routes, and seeds/tests covering the reviewer/admin workflow).

## 2025-10-18

✅ Completed: Enterprise boundary enforcement via trusted gateway middleware, forwarded-header validation, and documentation updates covering the SSO-only perimeter.
PR: feat/enterprise_boundary_enforcement

## 2025-10-19

- [x] TODO "pgvector GUC Bootstrap" - completed 2025-10-19 (release 0.8.0 adds migrations and verification checks for `app.pgvector_lists`).
- [x] TODO "Version Parity Automation" - completed 2025-10-19 (release 0.8.0 ships `scripts/check_version_parity.py`, Makefile wiring, and docs).
- [x] TODO "Uncertain Chat Validation Flow" - completed 2025-10-19 (release 0.8.0 captures low-confidence chats, follow-up prompts, admin drawer UX, and audit events).
- [x] TODO "Dictionary (Glossary) Update Semantics" - completed 2025-10-19 (release 0.8.0 adds POST upsert/PUT updates, inline editing, and rag event auditing).

## 2025-10-30

- [x] Audited `TODO.md` and confirmed no outstanding backlog items remain; updated the file to reference the completion log.
- [x] Verified the model catalog in `indices/model_catalog.json` maps families ⇄ models/aliases as required by the backlog item.
- [x] Confirmed disambiguation utilities (`retriever/models.py`, `retriever/resolver.py`) and scoped retrieval (`retriever/service.py`) implement the parser/resolver tasks.
- [x] Checked the API and client flow updates in `api/routes/chat.py`, `app/api/ask/route.ts`, `lib/ask-contract.ts`, `lib/ask-client.ts`, and `components/AnswerRenderer.tsx` to ensure clarification + multi-answer behaviour is live.
- [x] Reviewed ingestion tagging updates in `ingest/pipeline.py` and supporting docs (`docs/api/README.md`, `README.md`) covering the model-family flows.

## 2025-11-01

- [x] TODO "Glossary Enrichment" — completed 2025-11-01 (augmented glossary records with aliases/units/normalized product families, added inline glossary highlights to chat answers, refreshed seeds/tests, and documented the enriched dictionary workflow).

## 2025-10-18 — split_service_design
✅ Completed: Split the chat and admin UIs onto dedicated ports, added admin Make targets, and refreshed docs to emphasize independent builds.
PR: feat/split_service_design
