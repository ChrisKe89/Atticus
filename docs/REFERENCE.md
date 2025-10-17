# Repository Reference

## Folders

- [app/](../app/): Next.js application (App Router) with UI pages, route handlers, and global providers.
- [api/](../api/): FastAPI service exposing ingestion, chat, admin, and health endpoints.
- [atticus/](../atticus/): Shared Python package code (logging, metrics, configuration helpers).
- [components/](../components/): Reusable client-side UI components for the Next.js app.
- [content/](../content/): Source documents used for ingestion or examples.
- [docs/](./): Documentation, diagrams, and generated references for the project.
- [indices/](../indices/): Persisted vector index artifacts referenced by the retriever pipeline.
- [ingest/](../ingest/): Python ingestion workflows and utilities for preparing corpora.
- [retriever/](../retriever/): Retrieval-Augmented Generation core logic, including resolvers and embeddings.
- [prisma/](../prisma/): Prisma schema and migrations targeting the Postgres database.
- [scripts/](../scripts/): Automation helpers (quality checks, documentation exporters, tooling).
- [tests/](../tests/): Automated test suites for frontend and backend features.
- [reports/](../reports/): Generated logs, inventories, and audit artifacts (do not edit manually).

## Key Files

- [README.md](../README.md): High-level overview, setup instructions, and project goals.
- [CHANGELOG.md](../CHANGELOG.md): Semantic version history and notable release notes.
- [package.json](../package.json): Node.js dependencies, scripts, and Next.js configuration entry point.
- [pyproject.toml](../pyproject.toml): Python tooling configuration (Ruff, dependencies, scripts).
- [next.config.js](../next.config.js): Next.js build configuration and experimental flags.
- [Makefile](../Makefile): Composite developer workflows (database, linting, build orchestration).
- [tsconfig.json](../tsconfig.json): TypeScript compiler settings for the frontend workspace.
- [api/main.py](../api/main.py): FastAPI application factory wiring routers, middleware, and handlers.
- [app/layout.tsx](../app/layout.tsx): Global layout wrapper shared across Next.js pages.
- [app/api/ask/route.ts](../app/api/ask/route.ts): Next.js route handler proxying chat requests to the FastAPI `/ask` endpoint.

## How to Keep Docs Updated

- Add or update module headers and function/class docstrings in source files when behavior changes (Python docstrings, TypeScript JSDoc).
- Regenerate diagrams and reference data by re-running the autodoc workflow (phases 3–4) after modifying routes or architecture.
- Run formatting and linting (`npm run lint`, `npm run typecheck`, `npm run build`, plus documentation linters) to validate documentation integrity before committing.
