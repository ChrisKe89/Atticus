# ARCHITECTURE — Atticus

This document provides a **high‑level view of the Atticus system**, showing how data flows through ingestion, retrieval, and answer generation.

---

## System Overview

Atticus is a **Retrieval‑Augmented Generation (RAG)** platform.
It ingests content, builds a searchable vector index, retrieves relevant information on demand, and generates grounded answers.
The Next.js application is the canonical UI; historical static assets live under `archive/legacy-ui/` for reference only.

### Core Components

| Component                  | Responsibility                                                                                                                                                              |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Ingestion & Indexing**   | Parse → chunk → embed → persist vectors + metadata via Prisma migrations and Postgres/pgvector.                                                                             |
| **Retriever & Ranker**     | Vector search with optional lexical rerank; enforces metadata filters (`org_id`, `product`, `version`).                                                                     |
| **Generator**              | Drafts concise, sourced answers using the configured `GEN_MODEL`, respecting confidence thresholds.                                                                         |
| **API Layer**              | FastAPI exposes `/health`, `/ingest`, `/ask`, `/eval`, `/contact` with `/ask` streaming SSE payloads `{answer, sources, confidence, should_escalate, request_id}`.          |
| **Web UI**                 | Next.js App Router served from `/`, delivering chat, admin, settings, contact, and apps routes using shadcn/ui + Tailwind.                                                  |
| **Auth & Sessions**        | Auth.js magic-link flow with Prisma adapter, RLS-backed session storage, and RBAC-aware server actions.                                                                     |
| **Developer Tooling & CI** | Pre-commit (Ruff, mypy, ESLint, Prettier, markdownlint) plus GitHub Actions jobs (`frontend-quality`, `lint-test`, `pgvector-check`, `eval-gate`) mirroring `make quality`. |

---

## Data Flow

1. **Content Addition**
   New or updated documents are added to `content/` and named `YYYYMMDD_topic_version.ext`.

2. **Ingestion**
   Run `make ingest` to parse and chunk documents, compute embeddings, and update the index stored under `indices/`.

3. **Retrieval**
   When a user submits a query, the retriever searches the pgvector index and optionally applies a re-ranker to prioritize the most relevant chunks.

4. **Answer Generation**
   The selected context is passed to the generation model (default `gpt-4.1`) to produce a concise, sourced answer with inline citations.

5. **Escalation (if needed)**
   If the confidence score falls below the configured threshold, an escalation email is sent using SES SMTP.

### Ask flow (SSE)

1. Next.js `/api/ask` receives the chat request and validates payloads with shared DTOs in `lib/ask-contract.ts`.
2. The handler proxies the request to the FastAPI `/ask` endpoint, opening an SSE stream.
3. FastAPI streams JSON events (`answer`, `sources`, `progress`) until a terminating `done` event that includes `request_id`, `confidence`, and `should_escalate`.
4. The UI progressively renders tokens, logs the propagated `request_id`, and stores metadata for escalations.

---

## Supporting Services

- **Observability** — JSON logs (`logs/app.jsonl` and `logs/errors.jsonl`) with request IDs; metrics captured in evaluation runs and exported under `reports/`.
- **Snapshot & Rollback** — Index snapshots stored under `indices/` can be rolled back with `scripts/rollback.py`.
- **Evaluation & Audit Harness** — Retrieval evaluation against the gold set plus frontend audits (`reports/ci/*.json`) surfaced in CI artifacts.

---

## Security Considerations

- All secrets are loaded from `.env` and can be audited with `scripts/debug_env.py`.
- Escalation emails use SES SMTP credentials with IAM policies restricting senders and region (see [SECURITY.md](SECURITY.md)).
- Versioning is centralized in the [`VERSION`](VERSION) file and must align with `package.json` releases.

---

## Cross-References

- [AGENTS.md](AGENTS.md) — Detailed agent responsibilities and error policy.
- [OPERATIONS.md](OPERATIONS.md) — Runbooks and evaluation metrics.
- [README.md](README.md) — Setup instructions and Make targets.
