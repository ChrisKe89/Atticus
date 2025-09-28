# Completed Tasks — Atticus

This file is the **permanent log of completed tasks**.
Each entry includes the completion date and commit reference for traceability.

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

- [x] TODO "TROUBLESHOOTING.md — Add pgvector + Prisma troubleshooting (extension enablement, migration drift)." — completed 2025-09-30 (commit HEAD).

## 2025-10-04

- [x] TODO "`Makefile` — remove `ui` target (`http.server`); add Next.js scripts (`dev`, `build`, `start`); keep `api` until migration complete." — completed 2025-10-04 (commit HEAD).

- [x] TODO "`api/routes/chat.py` and `api/routes/ask.py` — consolidate; ensure request_id & should_escalate; remove unused import in api/routes/**init**.py." — completed 2025-10-04 (commit HEAD).
- [x] TODO "Dictionary/glossary admin — Design Prisma schema/API contracts for glossary records with approval workflow." — completed 2025-10-04 (commit HEAD).
- [x] TODO "Dictionary/glossary admin — Implement admin UI for propose/review/approve flows with RBAC checks." — completed 2025-10-04 (commit HEAD).
