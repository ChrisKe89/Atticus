# Atticus

> **Atticus for Sales Enablement** accelerates tender responses, keeps Sales self-sufficient, and frees Service/Marketing from ad-hoc requests.

Atticus is a Retrieval-Augmented Generation (RAG) assistant built on **Next.js**, **FastAPI**, **Postgres + pgvector**, **Prisma**, and **Auth.js**. It ingests content, indexes it with pgvector, and serves grounded answers with citations. When confidence is low the system sends a cautious partial answer and escalates via email.

---

## Quick Start

### 1. Bootstrap environment variables

Generate a local `.env` so secrets stay inside the repository:

```bash
python scripts/generate_env.py
python scripts/debug_env.py  # inspect precedence when overriding values
```

```powershell
python scripts/generate_env.py
python scripts/debug_env.py  # inspect precedence when overriding values
```

Populate SMTP settings for escalation email delivery:

- `CONTACT_EMAIL` – escalation recipient
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM` – SES SMTP credentials
- `SMTP_ALLOW_LIST` – comma-separated sender/recipient allow list
- `RAG_SERVICE_URL` – FastAPI retrieval service (defaults to `http://localhost:8000`)

### 2. Install dependencies

Install Python tooling (Ruff, mypy, pytest, etc.) and Node packages (Next.js workspace, shadcn/ui, Knip).

```bash
pip install -U pip pip-tools
pip-compile -U requirements.in
pip-sync requirements.txt
npm install
```

```powershell
pip install -U pip pip-tools
pip-compile -U requirements.in
pip-sync requirements.txt
npm install
```

### 3. Database and Prisma

Launch Postgres, apply migrations, and seed the default admin specified in `.env`.

```bash
make db.up
make db.migrate
make db.verify  # pgvector extension, dimension, IVFFlat probes
npm run prisma:generate
make db.seed
```

```powershell
make db.up
make db.migrate
make db.verify
npm run prisma:generate
make db.seed
```

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

### 4. Quality gates

`make quality` mirrors CI by running Ruff, mypy, pytest (>=90% coverage), Next.js lint/typecheck/build, and all audit scripts (Knip, icon usage, route inventory, Python dead-code audit).

```bash
make quality
```

```powershell
make quality
```

Pre-commit hooks now include Ruff, mypy, ESLint (Next + tailwindcss), Prettier (with tailwind sorting), and markdownlint. Install with `pre-commit install`.

### 5. Run services

Use separate terminals for the FastAPI backend and the Next.js UI.

```bash
make api        # FastAPI service on http://localhost:8000
make web-dev    # Next.js workspace on http://localhost:3000
```

```powershell
make api
make web-dev
```

### 6. Ingest, evaluate, and iterate

```bash
make ingest     # parse, chunk, embed, and update pgvector index
make eval       # run retrieval evaluation and emit metrics under eval/runs/
make seed       # generate deterministic seed manifest (seeds/seed_manifest.json)
```

### 7. Authenticate with magic link

Visit `http://localhost:3000/signin`, request a magic link for your provisioned email, and follow the link (from your inbox or `AUTH_DEBUG_MAILBOX_DIR`) to sign in. Admins can reach `/admin` to approve glossary entries.

### 8. `/api/ask` contract

The Next.js app exposes `/api/ask`, proxying the FastAPI retrieval service through server-sent events (SSE).

**Request**

```json
{
  "question": "What is the pilot timeline?",
  "contextHints": ["Managed print"],
  "topK": 8
}
```

**Response**

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

1. **Environment** – generate `.env` and update SMTP + Postgres credentials.
2. **Dependencies** – install Python + Node dependencies (`pip-sync` and `npm install`).
3. **Database** – run `make db.up && make db.migrate && make db.verify && make db.seed`.
4. **Quality** – run `make quality` locally before every PR. Fix formatting with `npm run format` (Prettier) and `make format` (Ruff) as needed.
5. **Run** – `make api` and `make web-dev` for local development.
6. **Observe** – watch `logs/app.jsonl`, `logs/errors.jsonl`, and the `/admin/metrics` dashboard.
7. **Release** – follow [RELEASE.md](RELEASE.md) for tagging and upgrade/rollback steps, confirming `VERSION` matches `package.json` before tagging.

Git pre-commit hooks enforce Ruff, mypy, ESLint, Prettier, markdownlint, and repository hygiene. Use `pre-commit run --all-files` to verify manually.

---

## CI and quality gates

GitHub Actions enforces:

- **frontend-quality** – Node 20 + Postgres service, running `npm run lint`, `npm run typecheck`, `npm run build`, and all audit scripts (`npm run audit:ts`, `npm run audit:icons`, `npm run audit:routes`, `npm run audit:py`). Audit outputs are uploaded as artifacts under `frontend-audit-reports`.
- **lint-test** – Python 3.12 toolchain running Ruff (lint + format check), mypy, pytest with ≥90% coverage, and pre-commit.
- **pgvector-check** – Applies Prisma migrations against pgvector-enabled Postgres and runs `make db.verify`.
- **eval-gate** – Retrieval evaluation regression checks (see [eval-gate.yml](.github/workflows/eval-gate.yml)).

Always confirm local `make quality` mirrors CI before pushing.

---

## Make targets

| Target                      | Description                                                         |
| --------------------------- | ------------------------------------------------------------------- |
| `make env`                  | Generate `.env` from defaults                                       |
| `make ingest`               | Parse, chunk, embed, and update the pgvector index                  |
| `make seed`                 | Generate deduplicated seed manifest (`seeds/seed_manifest.json`)    |
| `make eval`                 | Run retrieval evaluation and write metrics under `eval/runs/`       |
| `make api`                  | Start FastAPI backend                                               |
| `make web-dev`              | Run Next.js dev server (port 3000)                                  |
| `make app-dev`              | Alias for `make web-dev`                                            |
| `make db.up`                | Start Postgres (Docker)                                             |
| `make db.down`              | Stop Postgres (Docker)                                              |
| `make db.migrate`           | Run Prisma migrations                                               |
| `make db.verify`            | Ensure pgvector extension, dimensions, and IVFFlat settings         |
| `make db.seed`              | Seed default organization/admin                                     |
| `make help`                 | List available make targets                                         |
| `make web-build`            | Build the production Next.js bundle                                 |
| `make web-start`            | Start the built Next.js app                                         |
| `make web-lint`             | Run Next.js lint checks                                             |
| `make web-typecheck`        | Type-check the UI with TypeScript                                   |
| `make web-test`             | Run Vitest unit tests                                               |
| `make web-e2e`              | Run Playwright smoke tests                                          |
| `make smtp-test`            | Send an SES test email                                              |
| `make smoke`                | Run FastAPI health probe                                            |
| `make test.unit`            | Unit tests for hashing, config reload, mailer, chunker, seeds, eval |
| `make test.api`             | API contract tests (ask/contact/error schema/UI)                    |
| `make test`                 | Run pytest suite with coverage >=90%                                |
| `make lint` / `make format` | Ruff lint + auto-fix                                                |
| `make typecheck`            | Run mypy over atticus/api/ingest/retriever/eval                     |
| `make quality`              | Combined Python + Next quality gates and audits                     |
| `make web-audit`            | Run Node and Python audit scripts                                   |

---

## Observability & guardrails

- Every request receives a `request_id` propagated through logs, metrics, and escalation emails.
- Rate limiting enforces `RATE_LIMIT_REQUESTS` per `RATE_LIMIT_WINDOW_SECONDS`; extra calls return a structured `429 rate_limited` payload.
- Metrics (queries, escalations, latency) persist via `atticus.metrics.MetricsRecorder` and surface on `/admin/metrics` and CSV exports under `reports/`.
- Evaluation artifacts live under `eval/runs/<timestamp>/` and `reports/` for CI comparisons.

---

## Web UI

The Next.js application in `app/` is the supported interface.

- `app/page.tsx` hosts the streaming chat surface using `/api/ask` and renders citations.
- `app/contact/page.tsx` handles escalations to the FastAPI `/contact` endpoint.
- `app/admin/page.tsx` powers the glossary workflow and enforces Auth.js RBAC.

Legacy static assets live under `archive/legacy-ui/` for reference only.

---

## Auth & RBAC

- Email magic links deliver sign-in using SES SMTP credentials from `.env`.
- Admins (`ADMIN_EMAIL`) manage glossary terms at `/admin`; non-admins are redirected to `/`.
- Postgres Row Level Security gates glossary CRUD, user/session tables, and admin APIs by `org_id` + role.
- Use `withRlsContext(session, fn)` for Prisma calls that inherit user context.

Provisioning and rollback procedures are documented in [docs/runbooks/auth-rbac.md](docs/runbooks/auth-rbac.md).

---

## Documentation map

- [AGENTS.md](AGENTS.md) – architecture, environment settings, audit/CI requirements
- [ARCHITECTURE.md](ARCHITECTURE.md) – system diagram, data flow, SSE contract
- [OPERATIONS.md](OPERATIONS.md) – runbooks, metrics, and incident response
- [RELEASE.md](RELEASE.md) – release process, upgrade/rollback steps
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) – common setup, Auth.js, pgvector, SSE issues
- [REQUIREMENTS.md](REQUIREMENTS.md) – functional/non-functional requirements for the Next.js + pgvector stack
- [AUDIT_REPORT.md](AUDIT_REPORT.md) / [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) – remediation history
- [CHANGELOG.md](CHANGELOG.md) – release history
- [CONTRIBUTING.md](CONTRIBUTING.md) – contributor workflow
- [STYLEGUIDE.md](STYLEGUIDE.md) – code and writing standards
- [TODO.md](TODO.md) / [ToDo-Complete.md](ToDo-Complete.md) – authoritative backlog

---

## License

See [LICENSE](LICENSE).
