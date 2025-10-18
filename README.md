# Atticus

> **Atticus for Sales Enablement** accelerates tender responses, keeps Sales self-sufficient, and frees Service/Marketing from ad-hoc requests.

Atticus is a Retrieval-Augmented Generation (RAG) assistant built on **Next.js**, **FastAPI**, **Postgres + pgvector**, and **Prisma**.
It ingests content, indexes it with pgvector, and serves grounded answers with citations. When confidence is low the system sends a cautious partial answer and escalates via email.

> **Release 0.7.10** â€“ Locked the Next.js workspace in as the only UI, aligned API metadata with the central `VERSION` file, and refreshed operations docs for the split frontend/backend stack.
> Enterprise authentication and SSO are managed externally. This app assumes user access is handled upstream.

## Model Disambiguation Flows

- **Direct hit** â€” when a question names a specific model (for example, "Apeos C4570"), retrieval is scoped to that family and a single answer with family-tagged sources is returned.
- **Unclear** â€” if no confident match is found, `/api/ask` returns a `clarification` payload with the available families. The chat UI renders the clarification card and resubmits the prior question with an explicit `models` array when the user picks an option.
- **Multi-model** â€” if several models are detected or supplied, Atticus now decomposes the question into per-model prompts before retrieval. Each targeted prompt runs its own RAG pass via the multi-model query splitter (`retriever/query_splitter.py`), and the API responds with `answers[]`, keeping citations separate for each model while still providing the aggregated `sources` list for backwards compatibility.
- **Testing** â€” `tests/test_model_parser.py`, `tests/test_retrieval_filters.py`, `tests/test_chat_route.py`, `tests/test_ui_route.py`, and `tests/playwright/chat.spec.ts` lock these behaviours in place.

## Feedback Loop & Targeted Seeds

- **Flag unclear answers directly in chat.** The chat panel now exposes a _Flag for seeds_ action when an answer returns with citations. Atticus posts the flagged question, answer snippet, and cited paths to `/api/feedback`, which persists a `SeedRequest` row and generates a markdown scaffold under `content/seed_requests/` via `lib/seed-request-writer`.
- **Seed backlog management.** Admin reviewers gain a new _Seed requests_ tab in the operations console. Each entry shows captured context, regenerates the draft document on demand, and can be marked _completed_ once the curated documentation is published and ingested. Under the hood these actions call `/api/admin/seed-requests/:id/regenerate` and `/api/admin/seed-requests/:id/complete` to update Prisma + emit audit events.
- **Runbook.** Refer to `docs/runbooks/feedback-loop.md` for day-two operations, including regeneration, ingestion, and troubleshooting steps.

---

## Quick Start

1. Bootstrap environment variables

   Generate a local `.env` so secrets stay inside the repository:

   ```bash
   python scripts/generate_env.py
   python scripts/debug_env.py  # inspect precedence when overriding values
   ```

   Populate SMTP settings for escalation email delivery:
   - `CONTACT_EMAIL` â€“ escalation recipient
   - `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM` â€“ SES SMTP credentials
   - `SMTP_ALLOW_LIST` â€“ comma-separated sender/recipient allow list
   - `RAG_SERVICE_URL` â€“ FastAPI retrieval service (defaults to `http://localhost:8000`)

1. Install dependencies

   Install Python tooling (Ruff, mypy, pytest, etc.) and Node packages (Next.js workspace, shadcn/ui, Knip).

   ```powershell
   pip install -U pip pip-tools
   pip-compile -U requirements.in
   pip-sync requirements.txt
   npm install
   ```

1. Database and Prisma

   Launch Postgres, apply migrations, and seed baseline data.

   ```bash
   make db.up
   make db.migrate   # runs `prisma generate` before applying migrations
   # POSIX shells (bash/zsh): export DATABASE_URL before verification
   set -a
   . .env
   set +a
   make db.verify    # pgvector extension, dimension, IVFFlat probes
   make db.seed
   ```

   > Windows users: do **not** run the `set -a` snippetâ€”instead use the PowerShell block below (or rely on `make db.verify`, which now auto-loads `.env` values automatically).

   ```powershell
   make db.up
   make db.migrate
   Get-Content .env | ForEach-Object {
   if ($_ -and $_ -notmatch '^#') {
       $name, $value = $_.Split('=', 2)
       if ($value) { [System.Environment]::SetEnvironmentVariable($name.Trim(), $value.Trim(), 'Process') }
   }
   }
   make db.verify
   make db.seed
   ```

   `make db.verify` auto-loads `.env`, then shells out to `psql` (falling back to `docker compose exec postgres psql` when the CLI is unavailable) and will emit a notice if your pgvector build caps ANN indexes at 2K dimensions; upgrade the image to regain IVFFlat on 3K-dim embeddings.

   Run the verification SQL directly when debugging:

   ```bash
   psql "$DATABASE_URL" \
     -v expected_pgvector_dimension=${PGVECTOR_DIMENSION:-3072} \
     -v expected_pgvector_lists=${PGVECTOR_LISTS:-100} \
     -f scripts/verify_pgvector.sql
   ```

   ```powershell
   if (-not $env:PGVECTOR_DIMENSION) { $env:PGVECTOR_DIMENSION = 3072 }
   if (-not $env:PGVECTOR_LISTS) { $env:PGVECTOR_LISTS = 100 }
   psql "$env:DATABASE_URL" `
   -v expected_pgvector_dimension=$env:PGVECTOR_DIMENSION `
   -v expected_pgvector_lists=$env:PGVECTOR_LISTS `
   -f scripts/verify_pgvector.sql
   ```

1. Ingest documents

   Run ingestion once after the database is ready so the assistant has content to answer with; rerun whenever new documents land. `make eval` and `make seed` help during iteration.

  ```bash
  make ingest     # parse, chunk, embed, and update pgvector index
  make seed       # generate deterministic seed manifest (seeds/seed_manifest.json)
  make eval       # run retrieval evaluation (hybrid/vector) and emit metrics under eval/runs/
  ```

   Each evaluation run now benchmarks both the BM25+vector fusion strategy and pure vector search.
   Results for every mode live alongside per-query CSV/HTML artifacts, with a combined
   `retrieval_modes.json` summary for dashboards and regression tracking.

  > **Note:** The CED chunker now operates with zero token overlap by default
  > (`CHUNK_OVERLAP_TOKENS=0`). Override the environment variable if a
  > different stride is required for specialised corpora.

1. Run services

   Use separate terminals for the FastAPI backend and the Next.js UI.

   ```bash
   make api        # FastAPI service on http://localhost:8000
   make web-dev    # Next.js workspace on http://localhost:3000
   ```

   ```powershell
   make api
   make web-dev
   ```

1. Quality gates (before committing)

   ```bash
   make quality
   ```

   ```powershell
   make quality
   ```

  > `make quality` mirrors CI by running Ruff, mypy, pytest (>=90% coverage), Vitest unit tests, Next.js lint/typecheck/build, Playwright RBAC coverage, version parity checks, and all audit scripts (Knip, icon usage, route inventory, Python dead-code audit).
  > Pre-commit hooks now include Ruff, mypy, ESLint (Next + tailwindcss), Prettier (with tailwind sorting), and markdownlint. Install with `pre-commit install`.

1. Authenticate with magic link

1. `/api/ask` contract

   The Next.js app exposes `/api/ask`, proxying the FastAPI retrieval service through server-sent events (SSE).
   FastAPI still returns canonical JSON; the proxy synthesises `start`, `answer`, and `end` events so the UI can subscribe using a single streaming interface.

## Request

```json
{
  "question": "What is the pilot timeline?",
  "contextHints": ["Managed print"],
  "topK": 8
}
```

## Response

```json
{
  "answer": "...",
  "sources": [{ "path": "content/pilot.pdf", "page": 3 }],
  "confidence": 0.82,
  "request_id": "abc123",
  "should_escalate": false
}
```

Send `Accept: text/event-stream` to receive incremental events; `lib/ask-client.ts` handles SSE parsing, JSON fallback, and request-id logging.

---

## Developer workflow

1. **Environment**:
   - Generate `.env` and update SMTP + Postgres credentials.
2. **Dependencies**:
   - install Python + Node dependencies (`pip-sync` and `npm install`).
3. **Database**:
   - Run `make db.up && make db.migrate && make db.seed`.
   - Export `.env` before `make db.verify` so `DATABASE_URL` is available (`set -a; . .env; set +a` on POSIX shells, or use the PowerShell snippet in Quick Start on Windows).
4. **Quality**:
   - Run `make quality` locally before every PR.
   - Fix formatting with `npm run format` (Prettier) and `make format` (Ruff) as needed.
5. **Run**
   - `make api`
   - `make web-dev` for local development.
6. **Observe**
   - `logs/app.jsonl`
   - `logs/errors.jsonl`
   - `/admin/metrics` (dashboard)
7. **Release**
   - Follow [RELEASE.md](docs/RELEASE.md) for tagging.
   - Upgrade/rollback steps, confirming `VERSION` matches `package.json` before tagging.

8. **Git**
   - Git pre-commit hooks enforce Ruff, mypy, ESLint, Prettier, markdownlint, and repository hygiene
   - Use `pre-commit run --all-files` to verify manually.

## Legacy UI

The legacy HTML/CSS demo under `archive/legacy-ui/` is for reference only and excluded from builds and linting. The canonical UI is the Next.js app under `app/`. Avoid editing legacy files unless documenting history.

---

## Frontend design system

- Shared primitives built on shadcn/ui live under [`components/ui`](components/ui). Compose new surfaces with these building blocks instead of bespoke Tailwind markup to keep typography, spacing, and focus states consistent.
- Cards (`Card`, `CardHeader`, `CardContent`, etc.) wrap dashboard panels, admin glossaries, and contact forms with rounded borders and responsive padding.
- Badges (`Badge`) expose semantic variants (`default`, `success`, `warning`, `destructive`, etc.) for status chips, streaming indicators, and keyboard shortcut callouts.
- Buttons now support the `asChild` pattern for wrapping Next.js `Link` components, ensuring consistent styling for navigation pills and in-form actions.

---

## CI and quality gates

GitHub Actions enforces:

- **frontend-quality** â€“ Node 20 + Postgres service, running `npm run lint`, `npm run typecheck`, `npm run build`, and all audit scripts (`npm run audit:ts`, `npm run audit:icons`, `npm run audit:routes`, `npm run audit:py`). Audit outputs are uploaded as artifacts under `frontend-audit-reports`.
- **lint-test** â€“ Python 3.12 toolchain running Ruff (lint + format check), mypy, pytest with â‰¥90% coverage, and pre-commit.
- **pgvector-check** â€“ Applies Prisma migrations against pgvector-enabled Postgres and runs `make db.verify`.
- **eval-gate** â€“ Retrieval evaluation regression checks (see [eval-gate.yml](.github/workflows/eval-gate.yml)).

Always confirm local `make quality` mirrors CI before pushing.

---

## Make targets

| Target                      | Description                                                            |
| --------------------------- | ---------------------------------------------------------------------- |
| `make env`                  | Generate `.env` from defaults                                          |
| `make ingest`               | Parse, chunk, embed, and update the pgvector index                     |
| `make seed`                 | Generate deduplicated seed manifest (`seeds/seed_manifest.json`)       |
| `make eval`                 | Run retrieval evaluation (hybrid + vector fusion) and write metrics plus `retrieval_modes.json` under `eval/runs/` |
| `make api`                  | Start FastAPI backend                                                  |
| `make web-dev`              | Run Next.js dev server (port 3000)                                     |
| `make app-dev`              | Alias for `make web-dev`                                               |
| `make db.up`                | Start Postgres (Docker)                                                |
| `make db.down`              | Stop Postgres (Docker)                                                 |
| `make db.migrate`           | Run Prisma migrations                                                  |
| `make db.verify`            | Ensure pgvector extension, dimensions, and IVFFlat settings            |
| `make db.seed`              | Seed baseline demo content                                             |
| `make help`                 | List available make targets                                            |
| `make web-build`            | Build the production Next.js bundle                                    |
| `make web-start`            | Start the built Next.js app                                            |
| `make web-lint`             | Run Next.js lint checks                                                |
| `make web-typecheck`        | Type-check the UI with TypeScript                                      |
| `make web-test`             | Run Vitest unit tests                                                  |
| `make web-e2e`              | Run Playwright smoke tests                                             |
| `make smtp-test`            | Send an SES test email                                                 |
| `make smoke`                | Run FastAPI health probe                                               |
| `make test.unit`            | Unit tests for hashing, config reload, mailer, chunker, seeds, eval    |
| `make test.api`             | API contract tests (ask/contact/error schema/UI)                       |
| `make test`                 | Run pytest suite with coverage >=90%                                   |
| `make lint` / `make format` | Ruff lint + auto-fix                                                   |
| `make typecheck`            | Run mypy over atticus/api/ingest/retriever/eval                        |
| `make quality`              | Combined Python + Next quality gates, version-parity check, and audits |
| `make web-audit`            | Run Node and Python audit scripts                                      |

---

## Observability & guardrails

- Every request receives a `request_id` propagated through logs, metrics, and escalation emails.
- Rate limiting enforces `RATE_LIMIT_REQUESTS` per `RATE_LIMIT_WINDOW_SECONDS`; extra calls return a structured `429 rate_limited` payload.
- Metrics (queries, escalations, latency) persist via `atticus.metrics.MetricsRecorder` and surface on `/admin/metrics` and CSV exports under `reports/`.
- Evaluation artifacts live under `eval/runs/<timestamp>/` and `reports/` for CI comparisons.

---

## Web UI

The Next.js application in `app/` is the supported interface.

- `app/page.tsx` hosts the streaming chat surface using `/api/ask`, renders citations, and now injects glossary highlights (term definition, aliases, units, normalized product families) inline when responses reference curated terms.
- `app/contact/page.tsx` handles escalations to the FastAPI `/contact` endpoint.
- `app/admin/page.tsx` powers the glossary workflow and respects upstream reviewer/admin context.

Legacy static assets live under `archive/legacy-ui/` for reference only.

---

## Access Control

Enterprise authentication and SSO are managed upstream. The Atticus web workspace trusts the incoming request context and no longer performs session management or magic-link delivery internally.

## Admin Service (port 3101)

A separate Next.js workspace (`admin/`) now powers escalation review and answer curation. Run it alongside the main UI:

```bash
npm run dev --workspace admin    # http://localhost:3101
```

The console now includes four dedicated panels:

- **Embed new documents** — trigger partial or full corpus ingestion by sending POST `/api/ingest` jobs directly from the UI and capture manifest/index paths for auditing.
- **Escalated chats** — browse low-confidence transcripts, edit responses, and approve/reject escalations without impacting the main workspace.
- **Glossary library** — inspect and maintain the canonical `indices/dictionary.json` entries (terms, synonyms, aliases, units, normalized product families) before publishing updates; the chat surface consumes this metadata to decorate answers automatically.
- **Evaluation seeds** — review and edit `eval/gold_set.csv` via the admin API so retrieval benchmarks track the latest corpus changes.

Approved answers continue to append to `content/<family>/<model>.csv`, keeping the knowledge base synchronised with curator feedback.

## Content Management & Ingestion

Use the admin service ingestion panel to queue re-embeds after updating the `content/` tree:

- Submit one or more relative paths for partial refreshes or leave blank for full re-ingestion.
- Toggle “full refresh” to ignore the active manifest and rebuild embeddings from scratch.
- Capture ingestion output (documents processed, chunks indexed, manifest/index/snapshot paths) for downstream reporting.

---

## Documentation map

- [AGENTS.md](docs/AGENTS.md) â€“ architecture, environment settings, audit/CI requirements
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) â€“ system diagram, data flow, SSE contract
- [OPERATIONS.md](docs/OPERATIONS.md) â€“ runbooks, metrics, and incident response
- [RELEASE.md](docs/RELEASE.md) â€“ release process, upgrade/rollback steps
- [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) – common setup, pgvector, and SSE issues
- [REQUIREMENTS.md](docs/REQUIREMENTS.md) â€“ functional/non-functional requirements for the Next.js + pgvector stack
- [docs/AUDIT_REPORT.md](docs/AUDIT_REPORT.md) / [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) â€“ remediation history
- [CHANGELOG.md](CHANGELOG.md) â€“ release history
- [CONTRIBUTING.md](CONTRIBUTING.md) â€“ contributor workflow
- [STYLEGUIDE.md](docs/STYLEGUIDE.md) â€“ code and writing standards
- [ADMIN_SERVICE.md](docs/ADMIN_SERVICE.md) – standalone escalation tooling and reviewer workflow
- [TODO.md](TODO.md) / [TODO_COMPLETE.md](TODO_COMPLETE.md) â€“ authoritative backlog

---

## License

See [LICENSE](LICENSE).

## Token Count Test

```powershell
# GPT 4o-mini
python scripts/run_token_eval.py `
    --input "TOKEN_EVAL.xlsx" `
    --output "reports/4o_mini_ac7070_token_eval_atticus.csv" `
    --atticus-endpoint "http://localhost:8000/ask" `
    --model gpt-4o-mini `
    --tokenizer-model gpt-4o-mini
# GPT 4.1
python scripts/run_token_eval.py `
    --input "TOKEN_EVAL.xlsx" `
    --output "reports/gpt4_1_ac7070_token_eval_atticus.csv" `
    --atticus-endpoint "http://localhost:8000/ask" `
    --model gpt-4.1 `
    --tokenizer-model gpt-4.1

# GPT 5
python scripts/run_token_eval.py `
    --input "TOKEN_EVAL.xlsx" `
    --output "reports/gpt5_ac7070_token_eval_atticus.csv" `
    --atticus-endpoint "http://localhost:8000/ask" `
    --model gpt-5 `
    --tokenizer-model gpt-5
```
