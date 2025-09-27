# ARCHITECTURE — Atticus

This document provides a **high‑level view of the Atticus system**, showing how data flows through ingestion, retrieval, and answer generation.

---

## System Overview

Atticus is a **Retrieval‑Augmented Generation (RAG)** platform.
It ingests content, builds a searchable vector index, retrieves relevant information on demand, and generates grounded answers.

### Core Components

| Component | Responsibility |
|-----------|----------------|
| **Ingestion & Indexing** | Parse → chunk → embed → persist index using Postgres/pgvector with rich metadata. |
| **Retriever & Ranker** | Vector search with optional hybrid lexical re‑rank (BM25‑lite). |
| **Generator** | Drafts concise, sourced answers using GPT‑4.1 (or configured `GEN_MODEL`). |
| **API Layer** | FastAPI app exposing `/health`, `/ingest`, `/ask`, `/eval`, and `/contact` routes. |
| **Web UI** | Integrated front end served from `/`, providing a chat interface and escalation actions. |

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

---

## Supporting Services

* **Observability** — JSON logs (`logs/app.jsonl` and `logs/errors.jsonl`) and metrics collected during evaluation runs.
* **Snapshot & Rollback** — Index snapshots stored under `indices/` can be rolled back with `scripts/rollback.py`.
* **Evaluation Harness** — Ensures retrieval performance meets quality gates using `eval/goldset/*.jsonl`.

---

## Security Considerations

* All secrets are loaded from `.env` and can be audited with `scripts/debug_env.py`.
* Escalation emails use SES SMTP credentials with IAM policies restricting senders and region (see [SECURITY.md](SECURITY.md)).

---

## Cross-References

* [AGENTS.md](AGENTS.md) — Detailed agent responsibilities and error policy.
* [OPERATIONS.md](OPERATIONS.md) — Runbooks and evaluation metrics.
* [README.md](README.md) — Setup instructions and Make targets.
