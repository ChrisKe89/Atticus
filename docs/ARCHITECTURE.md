# ARCHITECTURE — Atticus

This document provides a **high‑level view of the Atticus system**, showing how data flows through ingestion, retrieval, and answer generation.

---

## System Overview

Atticus is a **Retrieval‑Augmented Generation (RAG)** platform.
It ingests content, builds a searchable vector index, retrieves relevant information on demand, and generates grounded answers.
The Next.js application is the canonical UI; historical static assets live under `archive/legacy-ui/` for reference only.

### Core Components

<!-- markdownlint-disable-next-line MD013 -->

| Component | Responsibility |
| --------- | -------------- |
| **Ingestion & Indexing** | Parse → chunk → embed → persist vectors + metadata via Prisma migrations and Postgres/pgvector. |
| **Retriever & Ranker** | Vector search with optional lexical rerank; enforces metadata filters (org_id, product,ersion). |
| **Generator** | Drafts concise, sourced answers using the configured GEN_MODEL, respecting confidence thresholds. |
| **API Layer** | FastAPI exposes /health plus mode-specific routers controlled by `SERVICE_MODE` (`chat` = /ingest, /ask, /eval, /contact, /ui; `admin` = /admin). `/ask` streams SSE payloads conforming to the shared JSON schema (`schemas/sse-events.schema.json`). |
| **Web UI** | Next.js App Router served from / on port 3000 (chat mode), delivering chat, settings, contact, and apps routes using shadcn/ui + Tailwind. |
| **Admin Service** | Dedicated Next.js workspace (port 9000) for escalated chat review, metrics, and content tooling. Deploy separately with `SERVICE_MODE=admin` for the API and `pnpm --filter admin dev` for the UI. |
| **Developer Tooling & CI** | Pre-commit (Ruff, mypy, ESLint, Prettier, markdownlint) plus GitHub Actions jobs (rontend-quality, lint-test, pgvector-check, val-gate) mirroring make quality. |

---

### Split Deployment

- **Chat bundle** – the primary Next.js app listens on port **3000** with `SERVICE_MODE=chat`. It exposes the chat UI, public APIs, and acts as the gateway for admin API calls consumed by the dedicated workspace.
- **Admin workspace** – the `admin/` Next.js project runs on port **9000** and targets the chat bundle via `ATTICUS_MAIN_BASE_URL` (defaults to `http://localhost:3000`). Links from the chat UI use `NEXT_PUBLIC_ADMIN_URL` so operators jump straight to the admin surface.
- **FastAPI** – toggles routers based on `SERVICE_MODE`. `chat` mode enables `/ingest`, `/ask`, `/eval`, `/contact`, and `/ui`; `admin` mode enables `/admin/**` for dictionary management, metrics, logs, and session views.

## Data Flow

1. **Content Addition**
   New or updated documents are added to `content/` and named `YYYYMMDD_topic_version.ext`.

2. **Ingestion**
   Run make ingest or trigger ingestion from /admin/content to parse and chunk documents, compute embeddings, and update the index stored under indexes/.

3. **Retrieval**
   When a user submits a query, the retriever searches the pgvector index and optionally applies a re-ranker to prioritize the most relevant chunks.

4. **Answer Generation**
   The selected context is passed to the generation model (default `gpt-4.1`) to produce a concise, sourced answer with inline citations.

5. **Escalation (if needed)**
   If the confidence score falls below the configured threshold, the conversation is written to the Prisma `Chat` table with `status='pending_review'`, stored `topSources[]`, and appended `RagEvent` audit rows. Admins can capture follow-up prompts, approve, or escalate these records from the Next.js `/admin` console, which also raises SES escalations when required.

### Ask flow (SSE)

1. Next.js `/api/ask` receives the chat request and validates payloads with shared DTOs in `lib/ask-contract.ts`.
2. The handler proxies the request to the FastAPI `/ask` endpoint.
3. FastAPI returns the canonical JSON payload; when the caller requested SSE, the Next.js proxy emits `start`, `answer`, and `end` events using the shared schema defined by `core/schemas/sse.py` (materialised as `schemas/sse-events.schema.json`).
4. The UI renders the received answer (currently delivered as a single chunk), logs the propagated `request_id`, and stores metadata for escalations.

---

## Supporting Services

- **Observability** — JSON logs (`logs/app.jsonl` and `logs/errors.jsonl`) with request IDs; metrics captured in evaluation runs and exported under `reports/`.
- **Snapshot & Rollback** — Index snapshots stored under `indices/` can be rolled back with `scripts/rollback.py`.
- **Evaluation & Audit Harness** — Retrieval evaluation against the gold set plus frontend audits (`reports/ci/*.json`) surfaced in CI artifacts.

---

## Security Considerations

- All secrets are loaded from `.env` and can be audited with `scripts/debug_env.py`.
- Escalation emails use SES SMTP credentials with IAM policies restricting senders and region (see [SECURITY.md](SECURITY.md)).
- Versioning is centralized in the [`VERSION`](../VERSION) file and must align with `package.json` releases.

---

## Cross-References

- [AGENTS.md](AGENTS.md) — Detailed agent responsibilities and error policy.
- [OPERATIONS.md](OPERATIONS.md) — Runbooks and evaluation metrics.
- [README.md](../README.md) — Setup instructions and Make targets.



