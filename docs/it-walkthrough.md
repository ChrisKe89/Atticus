# Atticus end-to-end walkthrough for IT demos

Use this guide to frame a full-stack demo of Atticus. Each stage lists the code and scripts that implement the capability so you can deep-link during your run-through.

## 1. Mission, personas, and architecture

- Product positioning, high-level data flow, and model disambiguation flows are summarized in the main README. Pair the opening narrative with the documented routing behaviour for multi-model answers. ([README.md](../README.md))
- FastAPI is bootstrapped in [`api/main.py`](../api/main.py), which wires the service lifespan, middleware, and `SERVICE_MODE` routing gates for chat vs. admin deployments.
- The customer chat front-end is the Next.js workspace rooted at [`app/page.tsx`](../app/page.tsx) and [`components/chat/chat-workspace.tsx`](../components/chat/chat-workspace.tsx), which mount the streaming chat panel.

## 2. Configuration and environment readiness

- `.env` creation, defaults, and fingerprinted secrets are managed in [`scripts/generate_env.py`](../scripts/generate_env.py); run it before any services start.
- [`scripts/debug_env.py`](../scripts/debug_env.py) prints a redacted configuration report using `core.config.environment_diagnostics`, which is useful for IT validation.
- Runtime settings (database URLs, SMTP, rate limits, vector sizes, service mode) live in [`core/config.py`](../core/config.py); highlight the `AppSettings` dataclass, service mode switch, and safety validators.
- The [`Makefile`](../Makefile) is the top-level entry point for `make db.up`, `make api`, `make web-dev`, and quality gates such as `make quality`.

## 3. Content ingestion lifecycle

- [`ingest/pipeline.py`](../ingest/pipeline.py) orchestrates document discovery, hashing, parsing, chunking, embedding, pgvector writes, manifest updates, and snapshotting. Walk through `ingest_corpus` to show reuse vs. refresh paths and model annotations.
- [`scripts/ingest_cli.py`](../scripts/ingest_cli.py) wraps the pipeline for CLI and CI usage, while [`api/routes/ingest.py`](../api/routes/ingest.py) exposes the same flow over HTTP with structured summaries.
- The ingestion manifest that drives change detection and snapshots is persisted via `Manifest` utilities in [`core/config.py`](../core/config.py) and is used by [`retriever/vector_store.py`](../retriever/vector_store.py) when loading metadata.

## 4. Retrieval, ranking, and answer generation

- [`retriever/vector_store.py`](../retriever/vector_store.py) merges pgvector cosine scores with BM25 lexical scoring, applies product-family filters, and caches results. Call out `_resolve_probes` and `_build_lexical_index` when discussing hybrid search tuning.
- [`retriever/service.py`](../retriever/service.py) formats contexts, computes dual-source confidence (`retrieval_conf` + `LLM_CONF_SWITCH` heuristic), and returns structured `Answer` payloads with escalation flags.
- [`retriever/query_splitter.py`](../retriever/query_splitter.py) and [`retriever/resolver.py`](../retriever/resolver.py) coordinate multi-model fan-out; the FastAPI `/ask` route invokes them via [`api/routes/chat.py`](../api/routes/chat.py).
- Server-Sent Events travel from FastAPI through the Next.js edge route in [`app/api/ask/route.ts`](../app/api/ask/route.ts), which normalises upstream errors, relays SSE chunks, and captures low-confidence chats via [`lib/chat-capture.ts`](../lib/chat-capture.ts).
- The browser consumes the stream with [`lib/ask-client.ts`](../lib/ask-client.ts) and [`components/chat/use-ask-stream.ts`](../components/chat/use-ask-stream.ts), which update the [`components/chat/chat-panel.tsx`](../components/chat/chat-panel.tsx) UI in real time and render citations through `AnswerRenderer`.

## 5. API surface, security, and escalation

- Middleware in [`api/middleware.py`](../api/middleware.py) assigns request/trace IDs, enforces per-identity rate limiting (`RateLimiter`), stamps rate-limit headers, and records latency/cost metrics.
- [`api/routes/chat.py`](../api/routes/chat.py) enforces validation rules, model clarification UX, glossary hits, and confidence aggregation before handing responses back to the client.
- [`api/routes/contact.py`](../api/routes/contact.py) bridges escalations into email by calling [`atticus/notify/mailer.py`](../atticus/notify/mailer.py), which enforces SMTP allow-lists, STARTTLS, and structured trace attachments.
- Admin-only operations (dictionary updates, evaluation seeds, metrics snapshots, log viewers) are gated through [`api/routes/admin.py`](../api/routes/admin.py) and surfaced in the admin Next.js UI panels such as [`admin/components/chat-review-board.tsx`](../admin/components/chat-review-board.tsx) and [`admin/components/metrics-dashboard.tsx`](../admin/components/metrics-dashboard.tsx).
- Rate-limit primitives used in middleware are implemented in [`api/rate_limit.py`](../api/rate_limit.py) and surfaced to clients via headers and admin dashboards.

## 6. Admin workspace and continuous feedback

- The admin SPA shells live in [`admin/app/layout.tsx`](../admin/app/layout.tsx) and [`admin/app/page.tsx`](../admin/app/page.tsx), pulling data through the `/api/admin` proxy endpoints under [`app/api/admin`](../app/api/admin).
- Seed curation and gold-set maintenance are handled client-side in [`admin/components/eval-seed-manager.tsx`](../admin/components/eval-seed-manager.tsx), which saves via `/api/eval-seeds` to back the evaluation harness.
- Escalated chat triage runs through [`lib/chat-capture.ts`](../lib/chat-capture.ts) on the Next.js edge (for capture) and is reviewed in [`admin/components/chat-review-board.tsx`](../admin/components/chat-review-board.tsx) with follow-up actions that call `/api/chats/:id/...` routes.
- Metrics refreshes in [`admin/components/metrics-dashboard.tsx`](../admin/components/metrics-dashboard.tsx) read from [`app/api/admin/metrics/route.ts`](../app/api/admin/metrics/route.ts), which forwards to FastAPI's `/admin/metrics` hook bound to [`atticus/metrics.py`](../atticus/metrics.py).

## 7. Observability, audits, and compliance

- JSON logging, rotating file handlers, and event helpers are centralised in [`atticus/logging.py`](../atticus/logging.py); middleware and routes use `log_event` / `log_error` consistently.
- Metrics aggregation and CSV snapshots are produced by [`atticus/metrics.py`](../atticus/metrics.py); the FastAPI lifespan in [`api/main.py`](../api/main.py) flushes them on shutdown.
- Structured error handling is unified in [`api/errors.py`](../api/errors.py), while rate-limit and request diagnostics are exposed to the admin UI via `/admin/sessions` in [`api/routes/admin.py`](../api/routes/admin.py).
- Evaluation reports and regression checks are orchestrated by [`scripts/eval_run.py`](../scripts/eval_run.py), which emits HTML/CSV artifacts under `eval/runs/` and enforces thresholds from `AppSettings`.

## 8. Testing and quality gates

- Pytest suites cover ingestion, retrieval, and routing—`tests/test_chat_route.py` validates rate limits, clarification flows, and response schema conformance, while other files in [`tests/`](../tests) cover hashing, mailer, chunker, and eval harness behaviour.
- Front-end unit and e2e coverage is exercised via `pnpm` scripts referenced in the [`Makefile`](../Makefile) (`web-test`, `web-e2e`, `admin-lint`, `admin-typecheck`).
- `make quality` (documented in the [`README`](../README.md) and implemented in the [`Makefile`](../Makefile)) runs Ruff, mypy, pytest (with ≥90% coverage), Next.js lint/typecheck/build, Playwright admin flows, and audit scripts to keep parity with CI.

## 9. Running the live demo

1. **Prep** – Run `make env`, `make db.up`, `make db.migrate`, and `make ingest` to ensure data and vectors are ready. The commands are defined in the [`Makefile`](../Makefile).
2. **Start services** – Launch the FastAPI backend (`make api`) and the chat frontend (`make web-dev`); optionally add `make admin-dev` for the reviewer console.
3. **Demo flow** – Ask a model-specific and a multi-model question in the chat UI (`components/chat/chat-panel.tsx`), trigger a low-confidence capture, then switch to the admin console to approve the chat (`admin/components/chat-review-board.tsx`).
4. **Close with observability** – Show the metrics dashboard refresh (`admin/components/metrics-dashboard.tsx`) and tail `logs/app.jsonl` to highlight structured logging configured by [`atticus/logging.py`](../atticus/logging.py).

Use these anchors to narrate how ingestion, retrieval, generation, escalation, and governance layers cooperate across the stack.
