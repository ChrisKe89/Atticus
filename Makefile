COMPOSE ?= docker compose

.PHONY: up down logs ingest eval build install lint format typecheck test check dev precommit compile

up:
	$(COMPOSE) up --build -d

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

ingest:
	$(COMPOSE) run --rm api python scripts/ingest.py

eval:
	$(COMPOSE) run --rm api python scripts/eval_run.py --json

build:
	$(COMPOSE) build

install:
	python -m pip install --upgrade pip
	python -m pip install -r requirements.txt

lint:
	ruff check .

format:
	ruff format .

typecheck:
	mypy

test:
	pytest

check: lint typecheck test

precommit:
	pre-commit run --all-files --show-diff-on-failure

compile:
	python -m piptools compile --resolver=backtracking requirements.in

dev:
	uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
