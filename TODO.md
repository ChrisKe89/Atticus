# TODO — Atticus

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

## Phase 1 — Parsing & routing (backend)

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

## Phase 2 — UI/UX (Next.js)

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

## Phase 3 — Ingestion & metadata (light touch)

1. **Ensure family tags exist on chunks.**

   * During CED ingestion (PDFs you’ve already loaded), confirm `product_family` and `models[]` are attached for:

     * C7070/C6570/C5570/C4570/C3570/C3070/C2570.
     * C8180/C7580/C6580.
   * If missing, add a light post-processor in `ingest/pipeline.py` that sets `product_family` from the catalog on import. (Paths for ingest modules present.) 

2. **Gold set extension.**

   * Add 6–10 **paired** gold questions (per family) into `eval/gold_set_improved.csv` to exercise single, unclear, and multi-model flows.

---

## Phase 4 - Tests (must-pass)

Completed on 2025-10-10 — Parser/resolver unit tests, API clarification coverage, and the Playwright chat flow are logged in `TODO_COMPLETE.md`.

---

## Phase 5 - Docs & ops

Completed on 2025-10-10 — Behaviour contract captured in AGENTS, user guides updated, changelog noted, and TODO items migrated to the archive.

---

## Phase 6 - Acceptance criteria (what "done" looks like)

Verified via automated direct/unclear/multi-model test cases during the 2025-10-10 quality run (see `TODO_COMPLETE.md`).

---
## Pointers for Codex (where to edit)

* **Backend (FastAPI/Next route boundary)**: `app/api/ask/route.ts`, `lib/ask-client.ts`, `retriever/models.py`, `retriever/service.py`, `retriever/generator.py`. 
* **UI**: `components/AnswerRenderer.tsx` (clarification card & multi-answer rendering). 
* **Ingest**: `ingest/pipeline.py` (ensure family tags) + `indices/model_catalog.json`. 
* **Tests**: `tests/test_chat_route.py`, `tests/test_ui_route.py`, `tests/playwright/*.spec.ts`, new `tests/test_model_parser.py`. 
* **Docs**: `AGENTS.md`, `docs/api/README.md`, `README.md`, `CHANGELOG.md`, `TODO.md`.

---

## Guardrails & edge cases

* If a user types a family name (e.g., “C7070 range”), resolve to family directly (don’t force a specific model).
* If a user picks **“give me a list”**, show the families first, then expandables for the exact models (use the catalog).
* If models span **different families**, **don’t merge** sources; answer independently per model.
* If no family matches but the question is clearly **general** (e.g., “What is a DADF?”), answer generically with neutral docs; otherwise ask to pick a family.

---

