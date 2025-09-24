# Makefile — Atticus
.PHONY: env ingest eval api ui e2e openapi smtp-test test lint format typecheck quality

PYTHON ?= python
XDIST_AVAILABLE := $(shell $(PYTHON) -c "import importlib.util; print(1 if importlib.util.find_spec('xdist') else 0)")
PYTEST_PARALLEL := $(if $(filter 1,$(XDIST_AVAILABLE)),-n auto,)

env:
	$(PYTHON) scripts/generate_env.py

smtp-test:
	$(PYTHON) -c "import sys;\ntry:\n    from atticus.notify.mailer import send_escalation\nexcept Exception as e:\n    print('TODO: implement atticus/notify/mailer.py'); sys.exit(1)\nelse:\n    send_escalation('Atticus SMTP test','This is a test from make smtp-test'); print('smtp ok')"

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
	@echo 'E2E stub complete - API/UI checks to be added once implemented.'

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
