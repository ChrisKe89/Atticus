# Atticus Documentation

## Adding New Content

1. Place documents inside the `content/` tree following the taxonomy in
   `AGENTS.md` §3.1.
2. Name files using `YYYYMMDD_topic_version.ext` for traceability.
3. Run `python scripts/ingest_cli.py` (or `make ingest`) to parse, chunk
   (defaults controlled by `config.yaml` / `.env`), embed, and update the
   index.
4. Review the ingestion report in `logs/app.jsonl` and commit the updated index
   snapshot plus `indices/manifest.json`.
5. Execute the evaluation harness with
   `python scripts/eval_run.py --json --output-dir eval/runs/manual` to confirm
   retrieval quality before tagging a release.
6. Regenerate API documentation with `python scripts/generate_api_docs.py` so
   the OpenAPI schema in `docs/api/openapi.json` stays in sync with the
   deployed code.

## Environment Setup

- Ensure Python 3.12 is active.
- Generate your `.env`:

```bash
python scripts/generate_env.py
# or overwrite an existing file:
python scripts/generate_env.py --force
# ignore host overrides entirely (useful when a stale OPENAI_API_KEY is exported):
python scripts/generate_env.py --force --ignore-env
```

### Required keys (created for you)

See **AGENTS.md** and comments in `scripts/generate_env.py` for detailed descriptions.
At minimum set: `CONTACT_EMAIL`, `SMTP_*` if you want escalation email to work.

### .env keys

The application reads all configuration from `.env` (host environment variables can override values unless you set `ATTICUS_ENV_PRIORITY=env`, which is the default). Use the diagnostics helper to trace which source won:

```bash
python scripts/debug_env.py
```

Sample output:

```json
{
  "env_file": "/workspace/Atticus/.env",
  "openai_api_key": {
    "conflict": true,
    "env_file_fingerprint": "2c1f3d8a8b0e",
    "fingerprint": "2c1f3d8a8b0e",
    "os_environ_fingerprint": "8a21d55c04bd",
    "present": true,
    "source": ".env"
  },
  "priority": "env",
  "repo_root": "/workspace/Atticus"
}
```

Set `ATTICUS_ENV_PRIORITY=os` if you explicitly want the live process environment to win over `.env` (e.g. in container orchestrators). Conflicts are recorded in `settings.secrets_report["OPENAI_API_KEY"]` for logging/tests.

The main `.env` keys are:

| Key | Description | Default |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI API key for embeddings/generation | (empty) |
| `OPENAI_MODEL` | Default LLM for agent/function calls | gpt-4.1 |
| `GEN_MODEL` | Generation model for answers | gpt-4.1 |
| `EMBED_MODEL` | Embedding model name | text-embedding-3-large |
| `EMBEDDING_MODEL_VERSION` | Embed model version pin | text-embedding-3-large@2025-01-15 |
| `CONFIDENCE_THRESHOLD` | Escalate when model confidence below this | 0.70 |
| `CHUNK_TARGET_TOKENS` | Target tokens per chunk | 512 |
| `CHUNK_MIN_TOKENS` | Minimum tokens per chunk | 256 |
| `CHUNK_OVERLAP_TOKENS` | Overlap between neighbor chunks | 100 |
| `MAX_CONTEXT_CHUNKS` | Chunks to stuff into context | 10 |
| `LOG_LEVEL` | Logging verbosity | INFO |
| `LOG_VERBOSE` | Include full chat content, token counts, and decision traces in logs (use with care) | 0 |
| `LOG_TRACE` | Emit additional step-by-step trace entries (debug) | 0 |
| `TIMEZONE` | Server/application timezone | UTC |
| `EVAL_REGRESSION_THRESHOLD` | % allowed regression on metrics | 3.0 |
| `CONTENT_DIR` | Path to ingestible content | ./content |
| `CONTACT_EMAIL` | Address exposed in UI "CONTACT" action | (empty) |
| `SMTP_HOST` | Mail server | (empty) |
| `SMTP_PORT` | Mail server port | 587 |
| `SMTP_USER` | SMTP username | (empty) |
| `SMTP_PASS` | SMTP password | (empty) |
| `SMTP_FROM` | From address for escalation emails | (empty) |
| `SMTP_TO` | To address for escalation emails (if different) | (empty) |

## Make Targets

The project defines the following convenience targets:

| Target | Does |
|---|---|
| `make env` | Create `.env` from defaults |
| `make ingest` | Ingest + index content from `CONTENT_DIR` |
| `make eval` | Run retrieval evaluation; write metrics under `eval/runs/` |
| `make api` | Start API (FastAPI/uvicorn) |
| `make ui` | Serve static UI (or API+UI if integrated) |
| `make smtp-test` | Send a test email using `.env` SMTP settings |
| `make e2e` | Ingest → Eval → API smoke → UI ping |
| `make openapi` | Regenerate OpenAPI schema |
| `make test` | Run unit tests (`pytest -q`) |
| `make lint` | Ruff lint + format check |
| `make format` | Apply Ruff formatting and fixes |
| `make typecheck` | Run `mypy` over core packages |

## Live Run

- Start the API locally:
  - `make api` → http://localhost:8000/
  - Docs: http://localhost:8000/docs
- Optional static UI only: `make ui` → http://localhost:8081/
- Examples: open `examples/dev.http` in your REST client to hit `/ask` and `/contact`.
- Observability:
  - Logs (JSONL): `logs/app.jsonl` (info), `logs/errors.jsonl` (errors)
  - Sessions view: `GET /admin/sessions?format=html|json`
  - Verbose logs (full Q/A, tokens, trace): set `LOG_VERBOSE=1` and optionally `LOG_TRACE=1` in `.env` and restart the API.

## Docker deployment

The repository ships with a Docker workflow for local or on-premise installs:

1. Ensure `.env` contains production-ready secrets (OpenAI key, SMTP, contact email).
2. Build the containers:

   ```bash
   docker compose build
   ```

3. Start the stack:

   ```bash
   docker compose up -d
   ```

   - `atticus-api` listens on `8000` and mounts `./content`, `indices`, and `logs`.
   - `atticus-nginx` fronts the API on ports `80/443` and runs health checks.

4. Tail logs: `docker compose logs -f api`.
5. Stop: `docker compose down` (add `-v` to clear named volumes).

To rebuild indices inside the container, exec into `atticus-api` and run the usual `make ingest` / `make eval` commands.

## Nginx reverse proxy

The `nginx/` directory contains a hardened reverse-proxy layer for TLS termination.

- `nginx/nginx.conf` expects the FastAPI service at `atticus-api:8000`.
- Place certificates in `nginx/certs/` (`fullchain.pem`, `privkey.pem` by default) or update the paths inside the config.
- Adjust the `server_name` directive to your domain before deploying.
- Reload configuration without downtime:

  ```bash
  docker compose exec nginx nginx -s reload
  ```

For environments where you already have a reverse proxy or load balancer, you can reuse the same configuration blocks.

## Frontend

- The UI is specified in **FRONTEND.md** and embedded in **TODO.md** with the exact HTML/CSS to materialize.
- Left side: collapsible menu with a single item **CONTACT**.
- Right side: chat panel; message stream scrolls above; input anchored at bottom.
- Theme pulls from `web/static/css/theme.css` (kept consistent with your provided stylesheet).
- CONTACT posts to `/contact` which sends an escalation email using `.env` (`CONTACT_EMAIL`, `SMTP_*`).

## Documentation Map (End-to-End)

- **AGENTS.md** – architecture, env, escalation, confidence policy
- **ARCHITECTURE.md** – components and data flow
- **OPERATIONS.md** – runbooks (ingest, eval, snapshot/rollback, logs)
- **FRONTEND.md** – UI spec and file placements
- **SECURITY.md** – secrets handling and redaction policy
- **TROUBLESHOOTING.md** – Windows/PDF/ingestion pitfalls
- **RELEASE.md** – release process & gates
- **CONTRIBUTING.md** / **STYLEGUIDE.md** – contributor rules & style

## Testing & Evaluation

### Unit tests
Run with `pytest -q`. Enforce ≥90% coverage across core packages unless an exemption is documented.
Coverage is enforced in CI and via `make test`.

Coverage exemptions (temporary, documented):
- Integration-heavy modules omitted until full suite lands:
  - `atticus/embeddings.py`, `atticus/faiss_index.py`, `atticus/metrics.py`, `atticus/tokenization.py`
  - `retriever/generator.py`, `retriever/vector_store.py`, `retriever/service.py`
  - `api/routes/admin.py`, `api/routes/eval.py`, `api/routes/ingest.py`, `api/utils.py`, `api/middleware.py`, `api/dependencies.py`
  - `atticus/config.py`, `atticus/logging.py`, `atticus/notify/mailer.py`
These are configured under `[tool.coverage.run].omit` in `pyproject.toml` and will be removed as tests are added.

### Ingestion smoke
`make ingest` then inspect logs for doc counts, chunk totals, and token range stats.

### Retrieval evaluation
- Place gold Q/A under `eval/goldset/*.jsonl`.
- Run `make eval` — metrics written to `eval/runs/<timestamp>/metrics.json`.
- Gate: fail CI if any metric regresses > `EVAL_REGRESSION_THRESHOLD` percent vs baseline (configured in `.env`).

### API contracts
- Regenerate OpenAPI: `make openapi`.
- Sample calls: see `examples/dev.http` for `/ask` and `/contact` requests.
