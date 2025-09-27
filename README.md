# Atticus\r\n\r\n> **Atticus for Sales Enablement** accelerates tender responses, keeps Sales self-sufficient, and frees Service/Marketing from ad-hoc requests.\r\n

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
Checks retrieval quality against the gold set and writes metrics to `eval/runs/<timestamp>/metrics.json`.

### 6. Run the service

Start the FastAPI backend and the Next.js UI in separate terminals.

```bash
make api   # http://localhost:8000
make ui    # http://localhost:3000
```

Docs remain at `http://localhost:8000/docs`; the web workspace runs on port 3000.

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
| `make ingest` | Parse, chunk, embed, and update index |
| `make eval` | Run retrieval evaluation and write metrics |
| `make api` | Start FastAPI backend |
| `make ui` | Run Next.js dev server (port 3000) |
| `make web-build` | Build the production Next.js bundle |
| `make web-start` | Start the built Next.js app |
| `make web-lint` | Run Next.js lint checks |
| `make web-typecheck` | Type-check the UI with TypeScript |
| `make smtp-test` | Send a test SES email |
| `make e2e` | Ingest -> Eval -> API/UI smoke (via `scripts/e2e_smoke.py`) |
| `make openapi` | Regenerate OpenAPI schema |
| `make test` | Run tests with >=90% coverage |
| `make lint` / `make format` | Lint and auto-fix with Ruff |
| `make typecheck` | Run static type checks |

---

## SMTP / SES Notes

* Use **SES SMTP credentials**. Do **not** use IAM access keys.  
* Region host must match the verified SES identity (e.g. `email-smtp.ap-southeast-2.amazonaws.com`).  
* In sandbox mode, recipients must also be verified.  
* Lock down SES with an IAM policy restricting `ses:FromAddress` to allowed senders and your region (see [SECURITY.md](SECURITY.md)).


## Web UI

The chat experience is served from the static assets under `web/static`.

- `web/static/index.html` hosts the Atticus chat surface that calls the `/ask` API for grounded answers.
- `web/static/contact.html` provides the escalation form backed by the `/contact` endpoint.
- `web/static/admin.html` keeps quick navigation shortcuts for operations staff.

Run `make api` and browse to `http://localhost:8000/static/index.html` (or your configured base URL) to load the interface.

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









