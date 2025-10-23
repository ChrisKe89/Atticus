# Root Repository Overview

This guide summarizes the top-level layout of the Atticus repository and highlights the automation entrypoints engineers reach for most often. Use it alongside `REPO_STRUCTURE.md` when you need deeper drilldowns into a specific package or service.

## Root directories and key files

| Entry | Purpose |
| ----- | ------- |
| `admin/` | Standalone Next.js workspace used by reviewers to triage escalations, manage glossary terms, and audit ingestion runs. |
| `api/` | FastAPI backend exposing chat, ingest, eval, and contact JSON routes plus shared middleware and schemas. |
| `app/` | Primary Next.js application delivering the chat surface, proxy API handlers, and shared providers/layout. |
| `archive/` | Historical assets (including the retired static UI) retained strictly for reference. |
| `atticus/` | Python helpers shared across services—for example environment settings loaders and structured logging utilities. |
| `components/` | Reusable React components grouped by feature areas (chat, admin, glossary) and shadcn/ui-based primitives. |
| `content/` | Canonical corpus of ingested source material bundled with sample seed documents. |
| `core/` | Configuration package centralizing YAML + environment merging, feature flags, and evaluation thresholds. |
| `docker/` | Container build artifacts such as the custom Postgres image compiled with pgvector support. |
| `docs/` | Architecture notes, runbooks, and contributor-facing references (including this overview). |
| `eval/` | Evaluation harnesses that benchmark retrieval quality (Recall@k, MRR@k) against the gold set. |
| `examples/` | HTTP request samples and cURL snippets for manual testing of chat and contact endpoints. |
| `indexes/` | Materialized vector indexes produced by ingestion jobs and mounted by the retriever. |
| `indices/` | Dictionary metadata and manifest files consumed by the retrieval and evaluation pipelines. |
| `ingest/` | Python ingestion pipeline (chunkers, embedders, summarizers) responsible for preparing content. |
| `lib/` | Front-end utilities, including streaming clients, auth helpers, and row-level security enforcement. |
| `logs/` | Structured JSON application and error logs written during local runs. |
| `nginx/` | Hardened reverse proxy configuration used by the Docker compose stack. |
| `prisma/` | Prisma schema, migrations, and seed hooks for auth, glossary, and admin review data. |
| `reports/` | Generated diagnostics—lint results, evaluation reports, CI artifacts—used to track quality gates. |
| `retriever/` | Retrieval service library that orchestrates vector search, reranking, and answer assembly. |
| `schemas/` | JSON schemas describing streaming payloads and admin review contracts. |
| `scripts/` | Operational CLIs supporting environment setup, audits, ingestion, evaluations, and release hygiene. |
| `seeds/` | Deterministic seed manifests produced by `make seed` to track curated ingestion inputs. |
| `tests/` | Automated test suites (pytest, Vitest, Playwright) covering API, ingestion, and UI flows. |
| `node_modules/` | Workspace dependencies installed by `pnpm install`; excluded from TypeScript compilation. |
| `CHANGELOG.md` | Human-readable change log aligned with semantic version increments. |
| `CONTRIBUTING.md` | Contribution guidelines covering environment setup, quality gates, and review expectations. |
| `LICENSE` | MIT license granting reuse rights with attribution. |
| `Makefile` | Unified automation entrypoint with targets for env bootstrapping, DB workflows, ingestion/eval runs, and quality checks. |
| `README.md` | High-level overview of Atticus, its RAG architecture, and operational workflow. |
| `REPO_STRUCTURE.md` | Curated map of the repository layout for quick navigation. |
| `TODO.md` / `TODO_COMPLETE.md` | Active backlog and dated completion log that govern autonomous execution. |
| `config.yaml` | Default runtime configuration covering ingestion, retrieval, logging, and evaluation thresholds. |
| `docker-compose.yml` | Development stack wiring Postgres/pgvector, FastAPI, admin UI, and proxy services with shared volumes. |
| `package.json` | Workspace definition for the main Next.js app, including scripts, dependencies, and Prisma hooks. |
| `pnpm-lock.yaml` / `requirements.txt` | Locked dependency sets for the Node and Python toolchains. |
| `pnpm-workspace.yaml` | Declares workspace packages so root installs cover both the main app and admin UI. |
| `pyproject.toml` | Python packaging metadata plus Ruff/mypy configuration. |
| `tailwind.config.js` / `postcss.config.js` | Front-end styling pipeline configuration. |
| `tsconfig.json` / `vitest.config.ts` | TypeScript compiler and front-end unit test harness settings. |
| `Atticus.code-workspace` | VS Code workspace definition aligning editor defaults (Ruff, pytest discovery, markdownlint). |
| `MANIFEST.txt` | Deployment/export manifest enumerating the assets packaged for distribution. |
| `VERSION` | Single source of truth for the project’s semantic version. |
| `components.json` | shadcn/ui generator configuration that pins component paths and style presets. |

## High-impact automation scripts

The `scripts/` directory contains many utilities; the following are the ones engineers touch most often:

- `scripts/generate_env.py` – Creates or refreshes `.env` files with hashed placeholders and sensible defaults for local development.
- `scripts/list_make_targets.py` – Lists available `Makefile` targets along with their short descriptions.
- `scripts/run_ingestion.py` / `scripts/ingest_cli.py` – Launch the ingestion pipeline to chunk, embed, and register new source documents.
- `scripts/eval_run.py` – Executes retrieval evaluation suites and writes Recall@k / MRR@k reports into `reports/`.
- `scripts/audit_unused.py` and `scripts/dead_code_audit.py` – Identify unused dependencies and Python modules for cleanup.
- `scripts/generate_api_docs.py` – Builds OpenAPI-derived reference documentation for the FastAPI service.
- `scripts/db_backup.py` / `scripts/db_restore.py` – Snapshot and restore the Postgres database used during local development.
- `scripts/make_seed.py` – Produces deterministic seed manifests for ingestion and stores them under `seeds/`.
- `scripts/update_changelog_from_todos.py` – Synchronizes `CHANGELOG.md` entries with completed tasks captured in `TODO_COMPLETE.md`.
- `scripts/test_health.py` and `scripts/e2e_smoke.py` – Smoke test the API, ingestion, and admin pathways to validate a fresh environment.

For a complete list, run `ls scripts/` or inspect the inline docstrings at the top of each helper.
