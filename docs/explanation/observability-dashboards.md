# Observability Dashboard Outline

Following `EXAMPLES_ONLY/server-monitoring.mdx`, this outline defines the key
dashboards for Atticus.

## Metrics sources

- `logs/metrics/metrics.csv` — ingestion/eval counters and latency.
- JSON logs — request/response events with `request_id` and status.
- SES escalation logs (`logs/escalations.jsonl`).

## Dashboard panels

1. **API health** — requests/min, error rate, latency p50/p95. Alert at error
   rate >5% or latency >2 s.
2. **Retrieval quality** — Precision@3, MRR, escalation rate. Compare against
   baseline using the latest eval run.
3. **Ingestion pipeline** — document counts processed per run, time per stage,
   failure counts.
4. **Escalations** — volume by category, SLA compliance (responded within 1 hour).
5. **System resources** — CPU/memory for API pods, FAISS index size.

## Tooling

- Preferred stack: Grafana + Prometheus (or CloudWatch if already in AWS).
- Schedule nightly export of `metrics.csv` into Prometheus via Pushgateway.
- Use Loki (or CloudWatch Logs) to ingest JSON logs for queryable request traces.

## Next steps

1. Define Prometheus scrape jobs and alerts in `infra/` manifests.
2. Automate dashboard provisioning via Grafana JSON definitions.
3. Document operational runbooks in `OPERATIONS.md` once dashboards go live.

This outline satisfies the TODO requirement and enables future implementation.
