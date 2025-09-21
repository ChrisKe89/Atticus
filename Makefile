COMPOSE ?= docker compose

.PHONY: up down logs ingest eval build

up:
	$(COMPOSE) up --build -d

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

ingest:
	$(COMPOSE) run --rm api python scripts/run_ingestion.py

eval:
	$(COMPOSE) run --rm api python -m eval.runner

build:
	$(COMPOSE) build
