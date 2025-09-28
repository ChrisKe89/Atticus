# Repository Structure Snapshot

Key directories to understand when working on Atticus.

- `app/`
  - `page.tsx` – streaming chat surface using the unified `/api/ask` contract.
  - `admin/` – admin dashboard with glossary workflow.
  - `contact/` – escalation form backed by the FastAPI `/contact` endpoint.
  - `signin/`, `settings/`, `apps/` – additional Next.js routes.
- `components/`
  - `chat/` – chat panel client components.
  - `glossary/` – admin glossary UI using shadcn-style primitives.
  - `ui/` – shared button/input/table components.
- `lib/`
  - `ask-client.ts`, `ask-contract.ts` – shared DTOs and streaming helpers.
  - `auth.ts`, `rls.ts`, `utils.ts` – auth, row-level security, and UI helpers.
- `api/`
  - `main.py` – FastAPI entry point wiring dependencies/middleware.
  - `routes/` – JSON APIs (`chat.py`, `contact.py`, `ingest.py`, etc.).
  - `middleware.py`, `schemas.py` – shared FastAPI utilities and contracts.
- `atticus/`, `retriever/`, `ingest/`, `eval/` – Python services and pipelines for ingestion, retrieval, and evaluation.
- `prisma/` – Prisma schema and migrations for auth/glossary data.
- `scripts/` – operational tooling (env generation, audits, ingestion, eval, etc.).
- `tests/`
  - Python pytest suites covering API contracts, ingestion utilities, and auth flows.
- `archive/legacy-ui/` – historical static HTML prototype retained for reference only.
- `content/`, `indices/`, `reports/`, `logs/` – document corpus, vector indices, evaluation artifacts, and log outputs.

Supporting docs live at the repository root (`README.md`, `AGENTS.md`, `ARCHITECTURE.md`, `OPERATIONS.md`, etc.).
