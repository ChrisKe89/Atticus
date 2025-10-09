# TODO — Atticus

This file replaces previous scattered TODOs and audit todos. It tracks only what is **still relevant**.

## 1) Glossary Seed & Runbook
**Goal:** deterministic baseline data + clear reset/rollback steps.

**Deliverables**
- Extend `prisma/seed.ts` with sample entries covering states: `approved`, `pending`, `rejected` (stable IDs).
- Add pytest `tests/test_seed_manifest.py` asserting baseline rows exist after `make db.seed`.
- Update docs:
  - `OPERATIONS.md` — how to reset/rollback glossary.
  - `docs/glossary-spec.md` — provisioning + rollback guidance.

**Acceptance**
- `make db.seed` produces deterministic rows; tests pass; docs explain reset/rollback for each environment.

---

## 2) Glossary UX Follow-through
**Goal:** visualise the review/approve path and capture decisions.

**Deliverables**
- Add Mermaid sequence diagram to `docs/glossary-spec.md`:
  ```mermaid
  sequenceDiagram
    participant Reviewer
    participant Admin
    Reviewer->>Admin: Submit glossary entry
    Admin->>System: Approve/Reject
    System-->>Reviewer: Status update + audit log
  ```
- Append ADR links or short “Decision Notes” explaining why this workflow was chosen.

**Acceptance**
- Spec renders with diagram + decisions; open follow-ups (notifications, audit UI) listed as backlog links.

---

## 3) RBAC Integration Coverage
**Goal:** prove role gates across **Next.js** and **FastAPI**.

**Deliverables**
- **Playwright** specs:
  - Non-admin → `/admin` and `/api/glossary` → `403/redirect`.
  - Admin can CRUD glossary.
- **API/route tests**:
  - Next route handlers with mocked sessions for each role.
  - FastAPI admin endpoints with invalid/missing admin token return `401/403` contracts.

**Acceptance**
- Tests fail on regressions; wired into CI via `make quality` / frontend job.

---

## 4) pgvector GUC Bootstrap
**Goal:** fresh DBs pass `make db.verify` without manual steps.

**Deliverables**
- Migration that ensures `set_config('app.pgvector_lists','100', true)` is present (idempotent).
- (Optional) Enhance `scripts/db_verify.py` to assert the GUC exists and print effective value.
- Update `OPERATIONS.md` with rollback/override notes.

**Acceptance**
- New environments pass `make db.verify`; docs show how to override the value.

---

## 5) Version Parity Automation
**Goal:** prevent drift between `VERSION`, `package.json`, and API metadata.

**Deliverables**
- Script `scripts/check_version_parity.py` to compare `VERSION` ↔ `package.json.version`.
- Makefile target `version-check`; include in `quality` (and optionally `verify`).
- Brief note in `README.md` / `RELEASE.md` about keeping versions in lockstep.

**Acceptance**
- CI fails when versions drift; local `make quality` surfaces mismatch immediately.

---

## 6) Admin Ops Console (Uncertain Chats, Tickets, Glossary)
**Goal:** give reviewers a single place to triage low-confidence chats, manage tickets, and edit glossary.

**Deliverables**
- **UI**: `/admin` with tabs — **Uncertain**, **Tickets**, **Glossary**.
  - Uncertain: table (date, user, question, confidence, top sources) + actions (**Approve**, **Ask Follow-up**, **Escalate**).
  - Tickets: list AExxx with status, assignee, last activity.
  - Glossary: search + inline edit (RBAC-gated).
- **API**:
  - `GET /api/admin/uncertain` — list chats where `confidence < CONFIDENCE_THRESHOLD` and `status='pending_review'`.
  - `POST /api/admin/uncertain/:id/approve` — marks reviewed; persists reviewer + timestamp.
  - `POST /api/admin/uncertain/:id/escalate` — creates/links AE ticket, logs action.
- **DB** (Prisma):
  - `chats`: add columns `confidence FLOAT`, `status TEXT DEFAULT 'ok'`, `reviewed_by`, `reviewed_at`.
  - `tickets`: ensure `AE` id, `status`, `assignee`, `linked_chat_id`.
- **RBAC**: only `admin` sees `/admin`; `reviewer` sees Uncertain+Glossary read, limited write.

**Acceptance**
- `reviewer` cannot access admin-only actions; `admin` can.
- Uncertain list populates from real chats; actions emit audit events; Playwright + API tests cover 403s for non-admins.

---

## 7) Uncertain Chat Validation Flow
**Goal:** make the “low confidence” path observable and correctable.

**Deliverables**
- Backend: whenever an answer is produced with `confidence < CONFIDENCE_THRESHOLD`, set `chats.status='pending_review'` and persist `{question, top_k sources, request_id}`.
- Route: `POST /api/admin/uncertain/:id/ask-followup` → stores a canonical follow-up prompt on the chat.
- UI: review drawer shows full context (question, answer, sources, request_id); buttons call the routes above.
- Tests: Playwright spec that (1) creates a low-confidence chat fixture, (2) sees it in Uncertain, (3) approves it, and (4) confirms status flips to `reviewed`.

**Acceptance**
- A low-confidence chat appears in Uncertain within one run; actions change status and are reflected in DB + UI; tests green.

---

## 8) Dictionary (Glossary) Update Semantics
**Goal:** safe, idempotent updates to existing terms; create on first write.

**Deliverables**
- API: `PUT /api/glossary/:id` (update by id) and `POST /api/glossary` (create); both require `admin`, fall back to **upsert** on unique `(org_id, term)`.
- Validation: reject empty `term`/`definition`; normalise whitespace; optional `synonyms[]`.
- Auditing: write to `rag_events` (actor, action, glossary_id, before/after).
- UI: inline edit row → optimistic update; toast on success/failure.

**Acceptance**
- Updating an existing term changes it in place (no duplicates); creating a non-existent term inserts it; RBAC enforced; audit row written.


Got it. Here’s a tight, codex-ready plan to add **model disambiguation + multi-model handling** to Atticus without making a mess. It’s phased so you can run it chunk-by-chunk.

# Phase 0 — Ground truth + contracts (prep)

1. **Define model families (authoritative).**

   * Create a small catalog (JSON or table) mapping names → families → aliases:

     * **Apeos C7070 range**: C7070, C6570, C5570, C4570, C3570, C3070, C2570. 
     * **Apeos C8180 series**: C8180, C7580, C6580. 
   * Store file path at `indices/model_catalog.json` (or DB table `model_catalog`), include: `{ canonical:"Apeos C4570", family:"C7070", aliases:["C4570","4570","Apeos C4570"] }`.

2. **Lock the API behavior (no surprises).**

   * Extend **/api/ask** to accept an optional `models` array and to return a new `clarification` field when model is unclear. See current API docs and contract location for `/ask`. 
   * Add response shape examples in `docs/api/README.md` (unclear → asks; multi-model → parallel answers). 

3. **Name the three user flows (for tests & docs).**

   * **Direct hit**: “Can the **Apeos C7070** do X?” → detect family C7070 → answer once.
   * **Unclear**: “Can the **printer** do X?” → return `clarification` prompt with selectable families.
   * **Multi-model**: “**Apeos C4570 and Apeos C6580**” → treat as two questions → answer both (C4570 ∈ C7070, C6580 ∈ C8180).

---
## FUTURE
# Phase 1 — Parsing & routing (backend)

1. **Model mention parser (pure function).**

   * New file: `retriever/models.py` (utilities already exist here; extend safely): add `extract_models(question: str) -> {models: set[str], families: set[str], confidence: float}`. Use strict patterns first (e.g., `Apeos\s+C\d{4}`), then fuzzy alias match via the catalog. (Repo has retriever pkg in place.) 

2. **Family resolver.**

   * New `resolver.py` in `retriever/` that maps found models → family set via the catalog (JSON or DB). Return `{ resolved_models, resolved_families, needs_clarification }`.

3. **/api/ask handler update.**

   * Touch `app/api/ask/route.ts` to accept `models?: string[]`. If absent, call parser. If `0` models and no strong hints → return `200` with `{ clarification: { message, options:[ "Apeos C7070 range", "Apeos C8180 series" ] }, request_id }` and **do not** trigger retrieval yet. Path exists. 
   * If `>1` distinct models/families → **fan-out**: run retrieval+generation per model and aggregate.

4. **Retrieval scoping.**

   * In `retriever/service.py` or `retriever/vector_store.py`, add a filter hook `filters.product_family in (...)` to limit chunks by family metadata you already store for CEDs (use existing metadata fields; CED ingest already distinguishes model rows/series). 

5. **Generator output shape (multi-answer).**

   * In `retriever/generator.py` ensure we can emit `{ answers: [ { model, text, sources[] } ] }` OR a single `{ answer }`. Keep `sources` per-answer to avoid cross-contamination. (AnswerRenderer can already handle lists; if not, adjust.)

---

# Phase 2 — UI/UX (Next.js)

1. **Chat flow tweaks.**

   * `components/AnswerRenderer.tsx`: render **clarification card** when `clarification` exists: copy “Which model are you referring to? If you like, I can provide a list of product families that I can assist with.” plus buttons:

     * “Apeos C7070 range”
     * “Apeos C8180 series”
     * “Show list of models” (opens modal).
   * If `answers[]` returned, render as collapsible sections per model with citations (you already stream sources). 

2. **Client ask flow.**

   * `lib/ask-client.ts`: support **follow-up POST** with selected `models` when user clicks a button in the clarification card. 

3. **Settings visibility remains gated** (unchanged, but keep your earlier constraint consistent). Paths exist under `app/settings`, `components/site-header.tsx`. 

---

# Phase 3 — Ingestion & metadata (light touch)

1. **Ensure family tags exist on chunks.**

   * During CED ingestion (PDFs you’ve already loaded), confirm `product_family` and `models[]` are attached for:

     * C7070/C6570/C5570/C4570/C3570/C3070/C2570.
     * C8180/C7580/C6580.
   * If missing, add a light post-processor in `ingest/pipeline.py` that sets `product_family` from the catalog on import. (Paths for ingest modules present.) 

2. **Gold set extension.**

   * Add 6–10 **paired** gold questions (per family) into `eval/gold_set_improved.csv` to exercise single, unclear, and multi-model flows.

---

# Phase 4 — Tests (must-pass)

1. **Unit**

   * `tests/test_model_parser.py`: direct hit, fuzzy alias, none → clarification, multi-model split.
   * `tests/test_retrieval_filters.py`: query constrained to a family returns only that family’s chunks.

2. **API/integration**

   * `tests/test_chat_route.py`:

     * unclear → returns `clarification` only (no retrieval).
     * multi-model → returns `answers[]` with model tags.
   * `tests/test_ui_route.py`: if you already have UI route tests, add snapshot checks for clarification JSON. 

3. **E2E (Playwright)**

   * Extend `tests/playwright/rbac.spec.ts` or add a new `chat.spec.ts`: type an unclear question → see clarification card → choose “Apeos C7070 range” → receive answer with C7070-family citations. (There’s already Playwright config present.) 

---

# Phase 5 — Docs & ops

1. **AGENTS.md** — add the behavior contract:

   * Ask clarifier when model unknown; treat multiple models as multiple sub-questions; scope retrieval by family; keep answers separate per model. (Doc file exists.) 

2. **README.md / docs/ATTICUS_DETAILED_GUIDE.md** — short “How Atticus interprets product names” section with examples.

3. **CHANGELOG.md** — note feature: “Model disambiguation + multi-model Q&A”.

4. **TODO.md → TODO_COMPLETE.md** — move tasks as they land (your doc workflow already calls this out). 

---

# Phase 6 — Acceptance criteria (what “done” looks like)

* **Direct**: “Can the **Apeos C7070** do X…?” → 1 answer, C7070 family-scoped citations pulled from the C7070 CED. 
* **Unclear**: “Can the **printer** do X…?” → UI shows clarifier with **C7070**/**C8180** options and a **show list** option. No retrieval occurs until user chooses.
* **Multi-model**: “**Apeos C4570 and Apeos C6580**” → 2 answers rendered, each with its own sources; C4570 from C7070 doc, C6580 from C8180 doc.
* **Tests**: unit + API + E2E cover the three flows; CI green with retrieval-gate unchanged. (Repo has the test harness & CI targets laid out.) 

---

# Pointers for Codex (where to edit)

* **Backend (FastAPI/Next route boundary)**: `app/api/ask/route.ts`, `lib/ask-client.ts`, `retriever/models.py`, `retriever/service.py`, `retriever/generator.py`. 
* **UI**: `components/AnswerRenderer.tsx` (clarification card & multi-answer rendering). 
* **Ingest**: `ingest/pipeline.py` (ensure family tags) + `indices/model_catalog.json`. 
* **Tests**: `tests/test_chat_route.py`, `tests/test_ui_route.py`, `tests/playwright/*.spec.ts`, new `tests/test_model_parser.py`. 
* **Docs**: `AGENTS.md`, `docs/api/README.md`, `README.md`, `CHANGELOG.md`, `TODO.md`.

---

# Guardrails & edge cases

* If a user types a family name (e.g., “C7070 range”), resolve to family directly (don’t force a specific model).
* If a user picks **“give me a list”**, show the families first, then expandables for the exact models (use the catalog).
* If models span **different families**, **don’t merge** sources; answer independently per model.
* If no family matches but the question is clearly **general** (e.g., “What is a DADF?”), answer generically with neutral docs; otherwise ask to pick a family.

---
