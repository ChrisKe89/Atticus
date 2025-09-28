# Makefile — Atticus
.PHONY: env ingest eval api e2e openapi smtp-test smoke test test.unit test.api lint format typecheck quality web-build web-start web-lint web-typecheck web-dev help \
        db.up db.down db.migrate db.seed db.verify seed web-test web-e2e

PYTHON ?= python
XDIST_AVAILABLE := $(shell $(PYTHON) -c "import importlib.util; print(1 if importlib.util.find_spec('xdist') else 0)")
PYTEST_PARALLEL := $(if $(filter 1,$(XDIST_AVAILABLE)),-n auto,)

DB_SERVICE ?= postgres
PGVECTOR_DIMENSION ?= 3072
PGVECTOR_LISTS ?= 100

env:
	$(PYTHON) scripts/generate_env.py

smtp-test:
	$(PYTHON) scripts/smtp_test.py

help:
	@echo "Available targets:"
	@python scripts/list_make_targets.py $(MAKEFILE_LIST)

api:
        $(PYTHON) -m uvicorn api.main:app --reload --port 8000


web-dev:
	@echo "Launching Next.js UI on http://localhost:3000 (expects API on :8000)"
	npm run dev

db.up:
	docker compose up -d $(DB_SERVICE)

db.down:
	docker compose stop $(DB_SERVICE)

db.migrate:
	npm run prisma:generate
	npm run db:migrate

db.verify:
	@if [ -z "$(DATABASE_URL)" ]; then \
	echo "DATABASE_URL is not set. Export it before running db.verify."; \
	exit 1; \
	fi
	psql "$(DATABASE_URL)" -v expected_pgvector_dimension=$(PGVECTOR_DIMENSION) -v expected_pgvector_lists=$(PGVECTOR_LISTS) -f scripts/verify_pgvector.sql

db.seed:
	npm run db:seed

ingest:
	$(PYTHON) scripts/ingest_cli.py

seed:
	$(PYTHON) scripts/make_seed.py

eval:
	$(PYTHON) scripts/eval_run.py

openapi:
	$(PYTHON) scripts/generate_api_docs.py

smoke:
	PYTHONPATH=. $(PYTHON) scripts/test_health.py

test.unit:
	PYTHONPATH=. pytest $(PYTEST_PARALLEL) --maxfail=1 --disable-warnings \
	tests/test_hashing.py \
	tests/test_config_reload.py \
	tests/test_mailer.py \
	tests/test_chunker.py \
	tests/test_seed_manifest.py \
	tests/test_eval_runner.py

test.api:
	PYTHONPATH=. pytest $(PYTEST_PARALLEL) --maxfail=1 --disable-warnings \
	       tests/test_chat_route.py \
	       tests/test_contact_route.py \
	       tests/test_error_schema.py \
	       tests/test_ui_route.py

test:
	pytest $(PYTEST_PARALLEL) --maxfail=1 --disable-warnings \
	       --cov=atticus --cov=api --cov=retriever \
	       --cov-report=term-missing --cov-fail-under=90

web-test:
	npm run test:unit

web-e2e:
	npm run test:e2e

e2e: env ingest eval
	$(PYTHON) scripts/e2e_smoke.py

# Local quality gates (mirror CI)
lint:
	ruff check .
	ruff format --check .

format:
	ruff format .
	ruff check . --fix

typecheck:
	mypy atticus api ingest retriever eval

quality: lint typecheck test

web-build:
	npm run build

web-start:
	npm run start

web-lint:
	npm run lint

web-typecheck:
	npm run typecheck
