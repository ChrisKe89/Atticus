# Re-ranker Deployment Strategy

Hybrid retrieval is optional in Atticus today. This plan formalises how we roll
out a cross-encoder reranker once model access is approved.

## Goals

- Improve grounding on long, keyword-heavy tenders without regressing latency by
  more than 300 ms.
- Maintain deterministic fallbacks when the reranker is unavailable.

## Architecture

1. **Model selection** — Start with `text-embedding-3-large` similarity +
   `bge-reranker-large` (via OpenAI Rerank API). Cache results per
   `(query, chunk_id)` for 24 hours to reduce cost.
2. **Integration point** — Extend `retriever/vector_store.py` with a
   `rank_candidates` hook. When `settings.enable_reranker` is true, call the
   rerank service after FAISS + BM25 candidate generation.
3. **Resilience** — Wrap API calls with a 1 s timeout and fall back to the
   baseline hybrid scoring if the reranker errors or times out. Log the event via
   `log_error(..., event="reranker_failure")`.

## Metrics & rollout

| Phase | Scope | Success Criteria |
|-------|-------|------------------|
| Pilot | 10% of `/ask` traffic in staging | Δ MRR ≥ +5%, latency p95 < 1.5 s |
| Beta  | All staging traffic + 20% production | Δ Precision@3 ≥ +7%, escalation rate ≤ baseline |
| GA    | 100% production | Regression guardrail: revert if escalation rate rises >3% |

Metrics are captured in `eval/runs/<timestamp>/metrics.json` and summarised in
`logs/metrics/metrics.csv`.

## Operational playbook

- Toggle via `.env` (`ENABLE_RERANKER=1`). CI runs evaluation twice (baseline vs
  rerank) and fails if GA guardrails breach.
- Update `README.md` and `CHANGELOG.md` when enabling in production.
- Document failure scenarios in `TROUBLESHOOTING.md` (e.g. API quota, latency).

## Future enhancements

- Investigate lightweight distillation to run the reranker locally for air-gapped
  deployments.
- Experiment with prompt-aware reranking (embedding + query rewrite) when the
  knowledge base grows beyond 100k chunks.
