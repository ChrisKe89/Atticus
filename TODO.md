# TODO - Atticus

All previously tracked items have been delivered and validated. See `TODO_COMPLETE.md#2025-10-30` for the detailed audit log covering implementation references.

Excellent — with the full `ALL_FILES.md` in hand, I can now generate a **new `TODO.md`** that is:

* Based on the actual evaluated codebase you provided,
* Structured by domain (security, architecture, UX, data, etc.),
* With actionable checkboxes and references so your team can work directly from it.

--

Excellent — that’s a very clean architectural move.
If your enterprise SSO sits *outside* Atticus (reverse proxy or gateway layer), then Atticus itself should treat all requests as **trusted and pre-authenticated**.

That means:

* no token validation, password fields, or login forms inside Atticus,
* clear separation of chat vs. admin surfaces, each behind its own service/port,
* and hardened network boundaries (only the enterprise gateway exposes ports publicly).

Here’s your **updated `TODO.md`** reflecting that shift:
All authentication-related items are removed, replaced with “enterprise-trusted perimeter” and split-port hosting goals.

---

> **Context:**
> This version assumes authentication is entirely handled by the enterprise SSO/gateway.
> Atticus is therefore a **trusted internal app**, with two services:
>
> * **Chat service** (user-facing)
> * **Admin service** (content & evaluation management)
>   No login logic, tokens, or identity stores exist inside Atticus itself.

---
Here’s the exact addition you should drop into your `TODO.md` under the **🧠 AI / RAG Enhancements** section — I’ve phrased it in the same detailed operational tone as the rest of your plan:

---

## 🧠 AI / RAG Enhancements

* [ ] **Implement Multi-Model Query Splitter**

  * Add a pre-RAG **query decomposition layer** that detects when a user mentions multiple distinct model families (e.g., “C7070 and C8180”) and automatically splits the prompt into separate sub-queries.
  * Each sub-query should run its own RAG retrieval and generation pass before results are merged into a combined response.
  * Core components:

    * `query_splitter.py` module under `agents/` or `retriever/`.
    * Detection via regex for FUJIFILM product codes (e.g., `C\d{4,5}`) or a small NER model for family tags.
    * Independent retrieval per sub-query using `run_rag_for_each()`.
    * Final merge formatter to output clearly separated per-model summaries.
  * Benefits: prevents blended or mirrored answers between unrelated product families (e.g., Shobu vs. Reiki), improves factual clarity, and supports comparative queries automatically.
* [ ] **Admin Page Extensions**

  * Embed new documents, view glossary entries, manage eval seeds.
* [ ] **Glossary Enrichment**

  * Aliases, units, and product family normalization.
  * Display glossary hits inline in chat answers.
* [ ] **Feedback Loop**

  * Capture unclear queries → add targeted seed documents.
* [ ] **Hybrid Retrieval**

  * Test BM25 + vector fusion, store eval metrics.
* [ ] **Prompt/Eval Governance**

  * Version prompt templates; pin MRR/nDCG thresholds in code.

---

Would you like me to also include a **“subtask breakdown”** for that item (e.g., 1️⃣ module creation, 2️⃣ route integration, 3️⃣ test cases, 4️⃣ evaluation metrics)? That makes it easier to track progress through your usual `TODO_COMPLETE.md` workflow.

## 🛡️ Security & Compliance

* [ ] **Enterprise Boundary Enforcement**

  * Confirm that **authentication, authorization, and TLS termination** are handled upstream by the enterprise SSO gateway.
  * Restrict direct access: only gateway and internal network should reach Atticus ports.
* [ ] **Split-Service Design**

  * Serve chat and admin panels on separate ports (e.g., `:8000` for API/chat, `:9000` for admin).
  * Admin UI must not be bundled with chat UI in Next.js build.
* [ ] **CORS Hardening** — Restrict allowed origins to the enterprise gateway only.
* [ ] **.env Hygiene**

  * Add `.env.example` documenting required variables; ensure `.env` is git-ignored.
* [ ] **Secret Scanning** — Add pre-commit/CI scan for leaked API keys.
* [ ] **Log Redaction** — Strip chat content from exception logs; include only request_id and route info.
* [ ] **Rate-Limit Headers** — Implement global limiters for incoming requests.
* [ ] **Docker Hardening** — Non-root, read-only filesystem, `HEALTHCHECK`, slim images.

---

## ⚙️ Build & CI/CD

* [ ] Pin and lock all dependencies (`requirements.txt`, `pnpm-lock.yaml`).
* [ ] Fail CI if lockfiles missing or outdated.
* [ ] Add ephemeral Postgres migration smoke test.
* [ ] Docker Compose smoke test (`make compose-up` → check `/health`).
* [ ] Multi-stage Docker builds with caching for deps.
* [ ] Release artifacts: `eval/reports`, `api/schema.json`, `docs/*.md`.

---

## 🧩 Architecture & Maintainability

* [ ] **Refactor Chat Flow** — unify `submit` and `clarify` into shared `useAskStream()` hook.
* [ ] **Central Config Loader** — single `core/config.py` (Pydantic `AppSettings`).
* [ ] **SSE Event Schema** — shared TS/Python schema for `answer` / `end` events.
* [ ] **Architecture Doc** — update `docs/ARCHITECTURE.md` for split-port deployment.
* [ ] **Admin UX** — move metrics/content into dedicated Next.js app on port 9000.
* [ ] Remove all legacy login, token, or RBAC references from code.
* [ ] Add `SERVICE_MODE` env var (`chat` or `admin`) to simplify containerization.

---

## 💾 Data & Retrieval

* [ ] Validate pgvector dimensions and probes match embedding model.
* [ ] Add indexes on metadata fields (`category`, `product`, etc.).
* [ ] Store embedding model/version in `seed_manifest.json`.
* [ ] Migrations smoke test in CI.
* [ ] Backup/restore job and integrity validation script.

---

## ⚡ Performance & Cost

* [ ] Add prompt and answer token caps (1.5K/1K).
* [ ] Cache last 10 normalized queries.
* [ ] Batch embeddings for ingestion efficiency.
* [ ] Tune pgvector probes dynamically.
* [ ] Disable chat input while streaming.
* [ ] Render evaluation dashboards as HTML in CI artifacts.
* [ ] Log tokens and cost estimates per 100 queries.

---

---

## 🧭 Observability & DX

* [ ] Add `request_id` and `trace_id` headers across services.
* [ ] Use structured JSON logging.
* [ ] Dead-code audits via `knip`, `ts-prune`; log results to `reports/quality/`.
* [ ] Update troubleshooting docs with split-port setup instructions.
* [ ] Add support playbook in `docs/OPERATIONS.md`.

---

## 📚 Documentation & Governance

* [ ] Update `README.md` and `ARCHITECTURE.md` for two-service model.
* [ ] Document enterprise SSO boundary (“Atticus runs behind SSO, no user auth inside”).
* [ ] Add `docs/SECURITY.md` for trusted network assumptions.
* [ ] Add `CHANGELOG.md` automation.
* [ ] Maintain `TODO_COMPLETE.md` with date-stamped completions.
* [ ] Expand `GLOSSARY.md` for dictionary agent baseline.

---

## 📅 Next Milestone

### **Atticus v0.9.0 — Dual-Service Release**

* Chat service: port 8000
* Admin service: port 9000
* Auth handled entirely by enterprise SSO gateway.
* Atticus internal trust boundary documented in `SECURITY.md`.

---
