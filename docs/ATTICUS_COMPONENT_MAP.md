# Atticus Prompting & Retrieval Map

This reference highlights the entry points for Atticus prompts, web UI surfaces, ingestion, embeddings, and vector search so you can navigate the codebase quickly.

## Prompt Templates & Generation
- `retriever/prompts.py` defines the versioned `PromptTemplate` registry (`atticus-v1`) including system and user message formats used by generation clients.【F:retriever/prompts.py†L1-L51】
- `retriever/generator.py` wraps OpenAI Responses, enforces token budgets, renders the active prompt template, and falls back to offline heuristics when no API key is configured.【F:retriever/generator.py†L1-L220】
- Prompt sizing and version selection are controlled by configuration (`core.config.AppSettings` via `config.yaml` defaults) and enforced when counting tokens inside the generator.【F:core/config.py†L63-L169】【F:retriever/generator.py†L32-L143】

## Key Web Application Surfaces
- `app/page.tsx` boots the chat workspace, while `components/chat/chat-workspace.tsx` frames the persistent chat layout.【F:app/page.tsx†L1-L5】【F:components/chat/chat-workspace.tsx†L1-L18】
- `components/chat/chat-panel.tsx` contains the primary chat interaction loop, including message state, streaming handlers, clarification follow-ups, and the welcome hero block shown before first use.【F:components/chat/chat-panel.tsx†L1-L200】
- Next.js route handlers in `app/api/ask/route.ts` proxy chat questions to the FastAPI backend, normalize upstream errors, and stream responses while capturing low-confidence answers for admin review.【F:app/api/ask/route.ts†L1-L220】
- Admin-specific flows (e.g., follow-up prompts) live under `app/api/admin/uncertain/[id]/*` and client components inside `components/admin/`, mirroring the operations surfaced in the console.

## Ingestion Pipeline
- `ingest/pipeline.py` orchestrates document discovery, parsing, chunking, metadata enrichment with the model catalog, embedding generation, and persistence, returning an `IngestionSummary` with manifest/index paths.【F:ingest/pipeline.py†L1-L200】
- `ingest/chunker.py` and `ingest/parsers/*` provide the document-to-chunk transformations that the pipeline calls before embedding.
- The ingestion run loads or refreshes manifests via `core.config.Manifest`, reuses unchanged chunks, annotates them with product metadata, snapshots results, and records embeddings for reindexing.【F:ingest/pipeline.py†L120-L200】

## Embedding Services
- `atticus/embeddings.py` exposes `EmbeddingClient`, which batches OpenAI embedding calls when credentials exist and otherwise produces deterministic offline vectors with consistent dimensionality.【F:atticus/embeddings.py†L1-L109】
- Embedding settings (model name, dimensions, batch size) come from `AppSettings` so both ingestion and retrieval reuse the same configuration.【F:atticus/embeddings.py†L19-L37】【F:core/config.py†L226-L283】

## Vector Storage & Retrieval
- `atticus/vector_db.py` implements `PgVectorRepository` and the `StoredChunk` dataclass, handling schema creation, metadata snapshots, and chunk persistence in Postgres/pgvector.【F:atticus/vector_db.py†L1-L240】
- `retriever/vector_store.py` loads chunk metadata into memory, builds lexical indexes, manages query caching, and executes hybrid vector/BM25 retrieval with dynamic probe tuning.【F:retriever/vector_store.py†L1-L240】
- Retrieval services combine the vector store, generator, and answer formatting inside `retriever/service.py` to assemble grounded responses and citations (see also `retriever/answer_format.py` for response shaping).

## Supporting References
- `app/api` routes surface ingestion triggers (content uploads, reingest) and admin reviews so the web console aligns with pipeline behavior.
- `scripts/` contains CLI entry points (`scripts/ingest.py`, `scripts/run_token_eval.py`) that wire into the same ingestion and retrieval modules for operational use.
