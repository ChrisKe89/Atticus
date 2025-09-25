# Makefile — Atticus
.PHONY: env ingest eval api ui e2e openapi smtp-test fmt lint type test cov quality docs smoke send-email next-ae log-escalation ui-ping release

PYTHON ?= python
export PYTHONPATH := src:$(PYTHONPATH)
XDIST_AVAILABLE := $(shell $(PYTHON) -c "import importlib.util; print(1 if importlib.util.find_spec('xdist') else 0)")
PYTEST_PARALLEL := $(if $(filter 1,$(XDIST_AVAILABLE)),-n auto,)

env:
	$(PYTHON) scripts/generate_env.py

smtp-test:
	$(PYTHON) -c "import sys;\ntry:\n    from atticus.notify.mailer import send_escalation\nexcept Exception as exc:\n    print(f'TODO: implement atticus/notify/mailer.py — {exc}'); sys.exit(1)\nelse:\n    send_escalation('Atticus SMTP test','This is a test from make smtp-test'); print('smtp ok')"

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

fmt:
	ruff format src tests scripts

lint:
	ruff check src tests scripts

type:
	mypy src/atticus src/api src/ingest src/retriever src/eval

test:
	pytest $(PYTEST_PARALLEL) --maxfail=1 --disable-warnings \
	--cov=atticus --cov=api --cov=retriever \
	--cov-report=term-missing --cov-fail-under=90

cov:
	pytest --cov=atticus --cov=api --cov=retriever --cov-report=term-missing --cov-report=html

quality: fmt lint type test cov

docs:
	npx --yes markdownlint-cli2 "**/*.md" "#node_modules" "#.venv"

smoke:
	pytest -q tests/test_smoke.py

send-email:
	@python scripts/send_email.py --subject "Test" --body "Atticus test email" || true

ui-ping:
	@python scripts/ui_ping.py

next-ae:
	@python scripts/next_ae_id.py

# Usage: make log-escalation AE=AE123 CAT=technical SCORE=0.61 \
#        Q="What is X?" A="Partial answer" TO="user@example.com" CC="manager@example.com" RID=req-123
log-escalation:
	@python scripts/log_escalation.py --ae-id "$(AE)" --category "$(CAT)" \\
		--confidence "$(SCORE)" --question "$(Q)" --answer "$(A)" \\
		--request-id "$(RID)" --recipients $(TO) --cc $(CC)

e2e: env ingest eval smoke ui-ping
	@echo 'E2E pipeline complete (ingest → eval → smoke → UI ping).'

release:
	cz bump --yes
	git push --follow-tags
