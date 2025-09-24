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

- [x] Added SES IAM policy region lock guidance to SECURITY.md and reinforced README cross-link - completed 2025-09-25 (commit be2c309).

> Continue logging future completed tasks below, grouped by date, to maintain a clear historical record.


