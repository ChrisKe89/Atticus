# Atticus\r\n\r\n> **Atticus for Sales Enablement** accelerates tender responses, keeps Sales self-sufficient, and frees Service/Marketing from ad-hoc requests.\r\n

> [!WARNING]
> This README still contains legacy FastAPI UI instructions. Refer to [AUDIT_REPORT.md](AUDIT_REPORT.md) finding FND-001 and [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for the authoritative remediation plan while the documentation rewrite is in progress.

## Purpose

Atticus is a Retrieval‑Augmented Generation (RAG) assistant designed to help **Sales** teams answer questions immediately, reduce interruptions to **Service** and **Marketing**, and speed up **tender** responses.  
It ingests your content, builds a searchable index, and generates grounded answers with citations. When confidence is low, Atticus provides a cautious partial answer and escalates via email (SES).

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
* `SMTP_ALLOW_LIST` – comma-separated allow list of approved sender/recipient emails or domains

### 2. Install dependencies

```bash
pip install -U pip pip-tools
pip-compile -U requirements.in
pip-sync requirements.txt
```
### 2a. Frontend (Next.js)

Install Node dependencies once to run the Next.js workspace.

```bash
npm install
make ui            # start the Next.js dev server (http://localhost:3000)
npm run build      # optional production build
```

```powershell
npm install
make ui            # uses the same Next.js dev server
npm run build
```

### 2b. Database & Prisma

Launch Postgres, apply migrations, and seed the default organization/admin specified in `.env`.

```bash
make db.up
make db.migrate
npm run prisma:generate
make db.seed
```

> The seed promotes `ADMIN_EMAIL` to the `ADMIN` role. Update `.env` before running in shared environments.


### 3. Add content

Drop documents into `content/`, naming them `YYYYMMDD_topic_version.ext` for easy traceability.  
Follow the taxonomy in [AGENTS.md](AGENTS.md#filefolder-glossary).

### 4. Ingest and index

```bash
make ingest
```
Parses, chunks, embeds, and updates the pgvector-backed index and metadata snapshot.

Generate a deterministic seed manifest for CI smoke tests:

```bash
make seed
```

The manifest (`seeds/seed_manifest.json`) captures CED chunk metadata (including SHA-256 hashes) without requiring embeddings.

### 5. Evaluate retrieval

```bash
make eval
```
Checks retrieval quality against the gold set and writes `metrics.csv`, `summary.json`,
and `metrics.html` into `eval/runs/<timestamp>/` for review and CI gating.

### 6. Run the service

Start the FastAPI backend and the Next.js UI in separate terminals.

```bash
make api   # http://localhost:8000
make ui    # http://localhost:3000
```

```powershell
make api
make ui
```

Docs remain at `http://localhost:8000/docs`; the web workspace runs on port 3000.

### 7. Authenticate with magic link

Visit `http://localhost:3000/signin` and request a magic link for your provisioned email. Open the link (from your inbox or `AUTH_DEBUG_MAILBOX_DIR`) to sign in and reach `/admin`.

---

## Order of Operations

From zero to production:

1. **Environment** – create and verify `.env`.
2. **Content** – add or update files under `content/`.
3. **Ingest** – `make ingest` to rebuild the index.
4. **Evaluate** – `make eval` and review metrics.
5. **Run** – `make api` for the backend and `make ui` for the Next.js workspace.
6. **Observe** – check `logs/app.jsonl` and `logs/errors.jsonl` or browse `/admin/sessions`.
7. **Release** – commit the updated `indices/manifest.json` and tag a new version.

Common shortcuts:
* Fresh machine -> `make env -> make ingest -> make eval -> make api -> make ui`
* Content changed -> `make ingest` (+ `make eval` if regression checks are needed)
* Code changed -> `make test`, `make lint`, `make typecheck`
* Full smoke test -> `make e2e` (runs ingest, eval, and API/UI smoke checks)

---

## Make Targets

| Target | Description |
|--------|------------|
| `make env` | Create `.env` from defaults |
| `make ingest` | Parse, chunk, embed, and update pgvector index |
| `make seed` | Generate deduplicated seed manifest (`seeds/seed_manifest.json`) |
| `make eval` | Run retrieval evaluation and write metrics |
| `make api` | Start FastAPI backend |
| `make ui` | Run Next.js dev server (port 3000) |
| `make db.up` | Start Postgres (Docker) |
| `make db.down` | Stop Postgres (Docker) |
| `make db.migrate` | Run Prisma migrations |
| `make db.seed` | Seed default organization/admin |
| `make web-build` | Build the production Next.js bundle |
| `make web-start` | Start the built Next.js app |
| `make web-lint` | Run Next.js lint checks |
| `make web-typecheck` | Type-check the UI with TypeScript |
| `make web-test` | Run Vitest unit tests for RBAC helpers |
| `make web-e2e` | Run Playwright RBAC/authentication smoke tests |
| `make smtp-test` | Send a test SES email |
| `make smoke` | Run a lightweight FastAPI health probe |
| `make test.unit` | Execute focused unit tests (hashing, config reload, mailer, seed manifest, eval outputs) |
| `make test.api` | Execute API contract tests (ask/contact/error schema/UI) |
| `make e2e` | Ingest -> Eval -> API/UI smoke (via `scripts/e2e_smoke.py`) |
| `make openapi` | Regenerate OpenAPI schema |
| `make test` | Run tests with >=90% coverage |
| `make lint` / `make format` | Lint and auto-fix with Ruff |
| `make typecheck` | Run static type checks |
| `npm run audit:ts` | Static usage graph via `knip` |
| `npm run audit:icons` | Validate Lucide icon tree-shaking configuration |
| `npm run audit:routes` | Emit Next.js route inventory (JSON) |
| `npm run audit:py` | Run Python dead-code audit (vulture) |

---

## Audit Artifacts

- [AUDIT_REPORT.md](AUDIT_REPORT.md) – detailed findings, evidence, and remediation estimates.
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) – phased rollout incorporating `TODO.md` items.

## SMTP / SES Notes

* Use **SES SMTP credentials**. Do **not** use IAM access keys.
* Region host must match the verified SES identity (e.g. `email-smtp.ap-southeast-2.amazonaws.com`).
* In sandbox mode, recipients must also be verified.
* Lock down SES with an IAM policy restricting `ses:FromAddress` to allowed senders and your region (see [SECURITY.md](SECURITY.md)).
* Populate `SMTP_ALLOW_LIST` with explicit recipients or domains to ensure escalations only reach approved addresses.

## Observability & Guardrails

* Every request receives a `trace_id` (mirrors `request_id`) propagated through logs, metrics, and escalation emails.
* The API enforces rate limiting (`RATE_LIMIT_REQUESTS` per `RATE_LIMIT_WINDOW_SECONDS`) using hashed identifiers; excess calls
  return a structured `429 rate_limited` payload.
* Metrics (queries, escalations, average and P95 latency) are persisted via `atticus.metrics.MetricsRecorder` and surfaced at
  `/admin/metrics` alongside latency histograms.
* Evaluation artifacts should be stored under `reports/` (see `reports/README.md` and the bundled `sample-eval.csv`).


## Web UI

The chat experience is served from the static assets under `web/static` while the production UI lives in the Next.js app.

- `web/static/index.html` hosts a lightweight chat surface that calls the unified `/ask` API returning `{answer, citations, confidence, should_escalate, request_id}`.
- `web/static/contact.html` provides the escalation form backed by the `/contact` endpoint.
- `web/static/admin.html` keeps quick navigation shortcuts for operations staff.

Run `make api` and browse to `http://localhost:8000/static/index.html` (or your configured base URL) to load the legacy interface.

---

## Auth & RBAC

Phase 3 introduces Auth.js + Prisma authentication:

- Email magic links deliver secure sign-in using the SMTP settings from `.env`.
- Admins (`ADMIN_EMAIL`) can manage glossary terms at `/admin`; non-admins are redirected to `/`.
- Postgres Row Level Security (RLS) gates glossary CRUD, user/session tables, and admin APIs by `org_id` + role.
- Use `withRlsContext(session, fn)` for Prisma calls that should inherit user context.

See [docs/runbooks/auth-rbac.md](docs/runbooks/auth-rbac.md) for provisioning, testing, and rollback procedures.

---

## Documentation Map

* [AGENTS.md](AGENTS.md) – architecture, environment settings, error policy
* [ATTICUS_DETAILED_GUIDE.md](docs/ATTICUS_DETAILED_GUIDE.md) – end-to-end flow, reranker behaviour, and roadmap parity
* [REMOTE_ACCESS.md](docs/REMOTE_ACCESS.md) – secure ways to reach a local instance from another PC
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









