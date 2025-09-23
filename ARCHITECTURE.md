# Architecture

Atticus is a Retrieval-Augmented Generation (RAG) system composed of:

- Ingestion & Indexing: parse → chunk → embed → persist (FAISS + metadata).
- Retriever & Ranker: vector search with optional hybrid lexical re-rank.
- Generator: offline summarizer with optional OpenAI Responses API.
- API: FastAPI app exposing `/health`, `/ingest`, `/ask`, `/eval`, `/contact`.
- UI: static web served under `/ui` with a CONTACT action.

Refer to `AGENTS.md` for environment variables and escalation policy.
