# Atticus\r\n\r\n> **Atticus for Sales Enablement** accelerates tender responses, keeps Sales self-sufficient, and frees Service/Marketing from ad-hoc requests.\r\n

## Purpose

Atticus is a Retrieval‑Augmented Generation (RAG) assistant designed to help **Sales** teams answer questions immediately, reduce interruptions to **Service** and **Marketing**, and speed up **tender** responses.  
It ingests your content, builds a searchable index, and generates grounded answers with citations. When confidence is low, Atticus provides a cautious partial answer and escalates via email (SES).

If the combined retrieval + generation confidence drops below `CONFIDENCE_THRESHOLD`, `/ask` returns `206 Partial` with
`escalated: true`, an `ae_id`, and routes the conversation to the appropriate team while logging the event to
`logs/escalations.*`.

## Quick Start

### 1. Environment

Generate a local `.env` so all secrets live in the project, not your shell:

```bash
python scripts/generate_env.py
# overwrite and ignore host env completely:
python scripts/generate_env.py --force --ignore-env
python scripts/debug_env.py   # confirm which source wins
```

Minimum settings for escalation email:
* `CONTACT_EMAIL` – escalation recipient
* `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM` – SES SMTP credentials (not IAM keys)

### 2. Install dependencies

```bash
pip install -U pip pip-tools
pip-compile -U requirements.in
pip-sync requirements.txt
```

### 3. Add content

Drop documents into `content/`, naming them `YYYYMMDD_topic_version.ext` for easy traceability.  
Follow the taxonomy in [AGENTS.md](AGENTS.md#filefolder-glossary).

### 4. Ingest and index

```bash
make ingest
```
Parses, chunks, embeds, and updates the vector index.

### 5. Evaluate retrieval

```bash
make eval
```
Checks retrieval quality against the gold set, writes metrics (including HitRate@5 and confidence bins) to
`eval/runs/<timestamp>/metrics.json`, and logs any regression exceeding the configured threshold.

### 6. Run the service

```bash
make api
```
Serves the API and UI at `http://localhost:8000` (docs at `/docs`).

---

## Order of Operations

From zero to production:

1. **Environment** – create and verify `.env`.
2. **Content** – add or update files under `content/`.
3. **Ingest** – `make ingest` to rebuild the index.
4. **Evaluate** – `make eval` and review metrics.
5. **Run** – `make api` to expose `/ask` and integrated UI.
6. **Observe** – check `logs/app.jsonl` and `logs/errors.jsonl` or browse `/admin/sessions`.
7. **Release** – commit the updated `indices/manifest.json` and tag a new version.

Common shortcuts:
* Fresh machine → `make env → make ingest → make eval → make api`
* Content changed → `make ingest` (+ `make eval` if regression checks are needed)
* Code changed → `make fmt`, `make lint`, `make type`, `make test`
* Full smoke test → `make quality`

---

## Make Targets

| Target | Description |
|--------|------------|
| `make env` | Create `.env` from defaults |
| `make ingest` | Parse, chunk, embed, and update index |
| `make eval` | Run retrieval evaluation and write metrics |
| `make api` | Start FastAPI and serve UI |
| `make ui` | Serve static UI assets only |
| `make smtp-test` | Send a test SES email |
| `make send-email` | Invoke the SMTP helper script with stub payload |
| `make openapi` | Regenerate OpenAPI schema |
| `make fmt` | Format Python sources with Ruff |
| `make lint` | Lint Python sources with Ruff |
| `make type` | Run mypy against the src/ layout |
| `make test` | Run tests with ≥90% coverage gate |
| `make cov` | Generate terminal + HTML coverage reports |
| `make quality` | Execute fmt → lint → type → test → cov |
| `make docs` | Run markdownlint checks on documentation |
| `make smoke` | Run API smoke tests covering 200 and 206 flows |
| `make ui-ping` | Validate the UI template contains the escalation banner |
| `make next-ae` | Print the next escalation identifier (`AE100`, `AE101`, …) |
| `make log-escalation` | Append an escalation entry to the JSONL/CSV logs |
| `make e2e` | Ingest → Eval → smoke tests → UI ping |
| `make release` | Bump version with Commitizen and push tags |

---

## Answer Contract

Atticus keeps responses short, grounded, and structured:

* **Clarifications**: if a query is ambiguous (too short, pronoun-heavy, or lacking product/workflow context) the API returns
  `clarification_needed=true` with a targeted follow-up question before attempting retrieval.
* **Answer payload**: `/ask` responds with a two-sentence `answer`, optional `bullets` (max three highlights), and up to three
  `citations` containing `source_path`, `page_number`, and headings. `request_id` is unique per call.
* **Partial answers**: when `confidence < CONFIDENCE_THRESHOLD`, the route emits `206 Partial`, prefixes the answer with
  “This may be incomplete…”, and includes `escalated=true` plus the `ae_id` used for email/log routing. Escalation emails use
  subjects `Escalation from Atticus: AE<INT> · {request_id}` so either identifier correlates the downstream logs.
* **UI behaviour**: chat bubbles render the summary, bullet list, and a “Sources” section; the escalation banner now triggers with
  the new structured payload.

---

## Observability & Telemetry

Atticus emits structured logs and spans by default:

* `LOG_VERBOSE=0` (default) prints human-readable console logs; set `LOG_VERBOSE=1` for JSON on stdout.
* `LOG_TRACE=1` or `OTEL_ENABLED=1` injects `trace_id`/`span_id` into every log line.
* Set `OTEL_EXPORTER_OTLP_ENDPOINT` (defaults to `http://localhost:4318/v1/traces`) and optional `OTEL_EXPORTER_OTLP_HEADERS` to push spans to your collector.
* `OTEL_TRACE_RATIO` controls sampling (0.0–1.0). Enable `OTEL_CONSOLE_EXPORT=1` to mirror spans to the console for local debugging.

Escalations always append structured JSON to `logs/escalations.jsonl` and CSV rows to `logs/escalations.csv`, both keyed by `request_id` and `ae_id`.

---

## Repository Layout

```
.
├── adr/                # Architecture decision records (see ADR 0001)
├── infra/              # Deployment stubs (Docker Compose, OTel collector notes)
├── scripts/            # CLI utilities (env generation, ingestion, escalation logging)
├── src/atticus         # Core configuration, logging, telemetry, notify modules
├── src/api             # FastAPI app, routes, middleware, error schema
├── src/ingest          # Chunking, parsers, and ingestion pipeline
├── src/retriever       # Retrieval services and vector store integration
├── src/eval            # Evaluation harness code (tests live in src/eval/harness)
├── eval/               # Baseline metrics, gold sets, and run artifacts
├── docs/               # Diátaxis docs (tutorials, how-to, reference, explanation)
├── logs/               # Structured JSON/CSV logs and metrics snapshots
├── tests/              # API/unit tests and error-schema coverage
└── web/                # Static UI assets and templates
```

---

## SMTP / SES Notes

* Use **SES SMTP credentials**. Do **not** use IAM access keys.  
* Region host must match the verified SES identity (e.g. `email-smtp.ap-southeast-2.amazonaws.com`).  
* In sandbox mode, recipients must also be verified.  
* Lock down SES with an IAM policy restricting `ses:FromAddress` to allowed senders and your region (see [SECURITY.md](SECURITY.md)).

---

## Documentation Map

* [AGENTS.md](AGENTS.md) – architecture, environment settings, error policy
* [System Overview](docs/explanation/system-overview.md) – end-to-end flow, reranker behaviour, and roadmap parity
* [Remote Access](docs/how-to/remote-access.md) – secure ways to reach a local instance from another PC
* [Getting Started tutorial](docs/tutorials/getting-started.md) – ingest and evaluate content step by step
* [API Reference](docs/reference/api/README.md) – OpenAPI schema and contract notes
* [Glossary](docs/reference/dictionary.yml) – canonical definitions for Atticus terminology
* [Escalation vs. Refusal Policy](docs/explanation/escalation-policy.md) – thresholds, categories, and workflow
* [Re-ranker Deployment Strategy](docs/explanation/reranker-deployment.md) – rollout plan and guardrails
* Enhancement outlines: [Socket.IO progress](docs/explanation/socketio-progress-evaluation.md), [Crawling UI](docs/explanation/crawling-ui-prototype.md), [MCP integration](docs/explanation/mcp-integration-plan.md), [Project rooms](docs/explanation/project-rooms-outline.md), [Observability dashboards](docs/explanation/observability-dashboards.md)
* [OPERATIONS.md](OPERATIONS.md) – runbooks and evaluation metrics guide
* [ARCHITECTURE.md](ARCHITECTURE.md) – high-level system diagram
* [SECURITY.md](SECURITY.md) – secrets handling and SES policies
* [TROUBLESHOOTING.md](TROUBLESHOOTING.md) – common setup and parsing issues
* [RELEASE.md](RELEASE.md) – release process and CI gates
* [CHANGELOG.md](CHANGELOG.md) – release history
* [CONTRIBUTING.md](CONTRIBUTING.md) – contributor workflow
* [STYLEGUIDE.md](STYLEGUIDE.md) – code and writing standards
* [TODO.md](TODO.md) / [ToDo-Complete.md](ToDo-Complete.md) – live and completed tasks
---

## License

See [LICENSE](LICENSE).









