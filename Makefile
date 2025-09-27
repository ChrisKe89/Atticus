# Makefile — Atticus
.PHONY: env ingest eval api ui e2e openapi smtp-test test lint format typecheck quality tailwind tailwind-watch

PYTHON ?= python
XDIST_AVAILABLE := $(shell $(PYTHON) -c "import importlib.util; print(1 if importlib.util.find_spec('xdist') else 0)")
PYTEST_PARALLEL := $(if $(filter 1,$(XDIST_AVAILABLE)),-n auto,)

env:
	$(PYTHON) scripts/generate_env.py

smtp-test:
	$(PYTHON) scripts/smtp_test.py

api:
	$(PYTHON) -m uvicorn api.main:app --reload --port 8000

ui:
	@echo Serving static UI on http://localhost:8081 (expects API on :8000)
	$(PYTHON) -m http.server 8081 --directory web

ingest:
	$(PYTHON) scripts/ingest_cli.py

eval:
	$(PYTHON) scripts/eval_run.py

openapi:
	$(PYTHON) scripts/generate_api_docs.py

test:
	pytest $(PYTEST_PARALLEL) --maxfail=1 --disable-warnings \
	       --cov=atticus --cov=api --cov=retriever \
	       --cov-report=term-missing --cov-fail-under=90

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

tailwind:
	npm run tailwind:build

tailwind-watch:
	npm run tailwind:watch
