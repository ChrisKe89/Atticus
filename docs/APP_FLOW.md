# Atticus End-to-End Flow

This document summarises how Atticus ingests source material, answers questions, and returns structured responses. Use it as a walkthrough when explaining the system to collaborators.

## High-Level Architecture

Atticus is a FastAPI service that exposes a `/ask` endpoint when the application runs in chat mode. The API lifespan initialises logging, metrics, CORS, and trusted gateway middleware before mounting routers for ingestion, chat, evaluation, contact, UI, and admin features.【F:api/main.py†L1-L105】

The runtime depends on:

- A content ingestion pipeline that parses documents, chunks them, embeds the text, and stores vectors plus metadata in PostgreSQL/pgvector.【F:ingest/pipeline.py†L1-L354】【F:atticus/vector_db.py†L1-L455】
- A retrieval layer that resolves product models, optionally splits questions, searches pgvector with hybrid scoring, and prepares context for generation.【F:retriever/resolver.py†L1-L118】【F:retriever/query_splitter.py†L1-L117】【F:retriever/vector_store.py†L1-L409】
- A generation layer that calls OpenAI (or a deterministic fallback) with a versioned prompt template, formats the answer, and deduplicates citations.【F:retriever/generator.py†L1-L200】【F:retriever/prompts.py†L1-L51】【F:retriever/answer_format.py†L1-L126】【F:retriever/citation_utils.py†L1-L59】
- A chat endpoint that orchestrates model resolution, retrieval, answer aggregation, glossary hits, logging, and the final API response contract.【F:api/routes/chat.py†L1-L320】【F:api/schemas.py†L40-L240】

The sections below follow this flow from ingestion through response formatting.

## Content Ingestion

### Document Discovery and Parsing

`ingest_corpus` is the entry point for updating the knowledge base. It loads application settings, initialises logging, and confirms the database connection before reading the existing manifest. It then enumerates target files (either supplied paths or everything under the configured content directory) and calculates SHA-256 hashes to detect reuse.【F:ingest/pipeline.py†L120-L182】 Reused documents are skipped while their stored chunks are marked with the new ingestion timestamp so they can be re-persisted without recomputation.【F:ingest/pipeline.py†L150-L177】 New or changed files are parsed into `ParsedDocument` instances via `parse_document`.

### Chunking Strategy (CED)

Each parsed document is split into chunks using the CED chunker. Prose sections are tokenised and sliced to the configured target size, with short trailing segments merged to stay above the minimum token threshold. Tables are decomposed into row-level chunks that retain header metadata, and footnotes are chunked separately. Every chunk carries breadcrumbs, section headings, pagination metadata, and a deterministic SHA computed from the payload to support deduplication.【F:ingest/chunker.py†L1-L225】

### Catalog Annotation and Embedding

Before embeddings are generated, Atticus extracts product model and family references from both documents and chunks using the model catalog. These labels are written into chunk metadata so downstream retrieval can filter on `product_family` and surface human-friendly labels.【F:ingest/pipeline.py†L46-L191】 Embeddings are produced in batches using `EmbeddingClient`, which tries OpenAI first and falls back to a deterministic hashing-based vector when no API key is configured, ensuring ingestion remains deterministic offline.【F:atticus/embeddings.py†L1-L109】

### Persistence and Manifest Updates

New `StoredChunk` objects combine chunk text, metadata, embedding vectors, and provenance. The pipeline persists them via `PgVectorRepository.replace_document`, which upserts document rows, clears prior chunks for the document, and inserts the new chunk set with both metadata JSON and vector columns populated. Supporting helpers also snapshot metadata to JSON, update the manifest (including corpus hash, counts, and embedding config), and clean up documents removed from the corpus.【F:ingest/pipeline.py†L200-L354】【F:atticus/vector_db.py†L329-L455】 The manifest and metadata snapshots provide immutable snapshots for audits and ingestion summaries.

## Retrieval and Question Routing

### Resolving Model Scope

Incoming questions may mention specific model codes or families. `resolve_models` matches explicit selections or extracts references from the natural-language question using the same catalog, producing `ModelScope` objects and a confidence score. If nothing can be resolved and the extraction confidence falls below a threshold, the chat route returns a clarification prompt listing available families.【F:retriever/resolver.py†L1-L118】【F:api/routes/chat.py†L130-L205】

### Splitting Questions by Scope

When multiple scopes are present (different model families or codes), `split_question` creates specialised prompts that instruct downstream retrieval to focus on a single scope. `run_rag_for_each` loops over the split prompts, calling `answer_question` for each to generate scoped answers while sharing base filters and UI hints.【F:retriever/query_splitter.py†L1-L117】 This allows the UI to present per-model answers or merge them into a combined response.

### Hybrid Vector + Lexical Search

`answer_question` constructs a `VectorStore`, which loads manifest metadata and cached chunk descriptors, ensuring the schema exists before querying. The store embeds the query (unless operating in lexical-only mode), performs a pgvector similarity search with adaptive IVFFlat probes, and blends those candidates with BM25 lexical scoring plus fuzzy matching. Hybrid scoring balances vector, lexical, and fuzzy signals, optionally re-ranking when the reranker is enabled. Metadata filters—such as `product_family` added during ingestion—are applied before results are returned. A small cache avoids recomputation for repeated queries.【F:retriever/service.py†L178-L283】【F:retriever/vector_store.py†L1-L409】 The retrieval layer also deduplicates citations to prevent repeated source references.【F:retriever/citation_utils.py†L1-L59】

## Generation and Answer Normalisation

`answer_question` formats the top chunks into context blocks and citation descriptors, then instantiates `GeneratorClient`. The client enforces prompt and answer token limits, renders the `atticus-v1` system/user prompts, and either calls the OpenAI Responses API or falls back to heuristic offline summarisation (including Q&A extraction and spec-style pattern searches). Confidence is calculated by blending retrieval and generation heuristics, and escalation is flagged when the score drops below the configured threshold.【F:retriever/service.py†L228-L283】【F:retriever/generator.py†L29-L200】【F:retriever/prompts.py†L8-L51】

Before returning, responses are normalised: inline citation remnants and ad-hoc “Sources” sections are stripped, lists are reflowed, and Markdown numbering is stabilised for UI rendering.【F:retriever/answer_format.py†L1-L126】 The deduplicated citation objects accompany the formatted answer.

## Chat Endpoint Orchestration

The FastAPI `/ask` handler validates the question, enforces token limits, and resolves model scopes. If clarification is required it returns a `ClarificationPayload`. Otherwise it retrieves answers for each scope, cleans answers to avoid contradictory “no information” statements across scopes, aggregates confidence/escalation flags, truncates the combined answer to the configured token cap, and attaches glossary hits derived from predefined entries. It also records metrics (prompt/answer token counts, confidence, escalation) via structured logs before returning the response.【F:api/routes/chat.py†L79-L320】

## Response Contract

Clients receive an `AskResponse` object that includes the primary answer string, per-scope answers (each with confidence, escalation flag, model metadata, and structured `AskSource` citations), optional clarification prompts, glossary hits, and the request ID needed for tracing. This schema is defined in `api/schemas.py`, which also documents the shapes of glossary hits and source references consumed by the UI.【F:api/schemas.py†L40-L240】

## Putting It Together

1. **Ingest content** using `ingest_corpus` to populate pgvector and refresh the manifest. Chunks now carry product-family metadata and embeddings for hybrid search.【F:ingest/pipeline.py†L120-L354】【F:atticus/vector_db.py†L329-L455】
2. **Accept a question** at `/ask`. The route validates input, resolves model scopes, and either asks for clarification or proceeds with scoped RAG execution.【F:api/routes/chat.py†L146-L205】
3. **Retrieve context** with the hybrid `VectorStore`, combining embedding similarity, BM25, and fuzzy signals while applying metadata filters.【F:retriever/vector_store.py†L252-L409】
4. **Generate the answer** through `GeneratorClient`, format it for Markdown consumption, dedupe citations, and compute a blended confidence score.【F:retriever/service.py†L228-L283】【F:retriever/generator.py†L29-L200】【F:retriever/answer_format.py†L1-L126】
5. **Return the structured payload** defined by `AskResponse`, including per-scope answers, glossary hits, and citations for the UI.【F:api/schemas.py†L90-L110】

Walking through these steps with teammates provides a clear picture of how Atticus turns ingested technical collateral into trustworthy, explainable answers.
