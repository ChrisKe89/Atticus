# OPERATIONS — Atticus

This document provides **day‑to‑day runbooks** and a detailed guide for interpreting evaluation metrics.
It complements [README.md](README.md) for setup and [AGENTS.md](AGENTS.md) for architecture.

---

## Ingest & Index

1. Add or update source files under `content/` using `YYYYMMDD_topic_version.ext` naming.
2. Run ingestion:

   ```bash
   make ingest
   ```

   This parses, chunks, embeds, and updates the vector index.
3. Check logs in `logs/app.jsonl` for document counts, chunk totals, and token ranges.
4. When ready for release, commit the updated `indices/` snapshot and `indices/manifest.json`.

---

## Evaluate Retrieval

1. Ensure gold Q/A sets exist under `eval/goldset/*.jsonl`.
2. Run evaluation:

   ```bash
   make eval
   ```

   Results are written to `eval/runs/<timestamp>/metrics.json`.
3. Compare against baseline metrics. CI will fail if regression exceeds `EVAL_REGRESSION_THRESHOLD`.

Use the [Evaluation Metrics Interpretation](#evaluation-metrics-interpretation) section below to understand the metrics.

---

## API & UI Operations

* Start the API and integrated UI:

  ```bash
  make api
  ```

  Available at `http://localhost:8000` (OpenAPI docs at `/docs`).
* If the UI is ever split out, reintroduce `make ui` and update the port mapping.
* To run a full smoke test (ingest → eval → API/UI check):

  ```bash
  make e2e
  ```

---

## Escalation Email (SES)

* Requires valid SES **SMTP credentials** (not IAM keys).
* Ensure the `CONTACT_EMAIL` and all `SMTP_*` environment variables are correctly set in `.env`.
* The SES identity for `SMTP_FROM` must be verified; sandbox mode also requires verified recipients.
* For security, lock down SES with an IAM policy restricting `ses:FromAddress` to approved senders and region (see [SECURITY.md](SECURITY.md)).

---

## Escalation Monitoring

* Partial responses return **206** with an `ae_id` and `escalated: true`.
* Each escalation is logged to `logs/escalations.jsonl` (JSON lines) and `logs/escalations.csv` (reporting).
* Generate new IDs with `make next-ae`; backfill logs via `make log-escalation AE=AE123 CAT=technical SCORE=0.61 Q="..." A="..." TO="user@example.com" RID=req-123`.
* `make send-email` (or `python scripts/send_email.py`) exercises the SMTP helper without touching application code.
* Email subjects follow `Escalation from Atticus: AE<INT> · {request_id}` so any identifier surfaces the correlated logs.

---

## Snapshot & Rollback

1. Snapshot the `indices/` directory during each release.
2. To revert to a previous snapshot:

   ```bash
   python scripts/rollback.py --manifest indices/manifest.json
   ```

3. After rollback, run a smoke evaluation:

   ```bash
   make eval
   ```

   and test a few known gold queries with `/ask`.

---

## Observability & Debugging

* **Logs**
  * Info: `logs/app.jsonl`
  * Errors: `logs/errors.jsonl`
* **Sessions view**
  * `GET /admin/sessions?format=html|json`
* **Tracing & telemetry**
  * Set `LOG_VERBOSE=1` for JSON console logs; `LOG_TRACE=1` or `OTEL_ENABLED=1` injects span IDs.
  * Configure `OTEL_EXPORTER_OTLP_ENDPOINT` (default `http://localhost:4318/v1/traces`) and optional `OTEL_EXPORTER_OTLP_HEADERS` to forward spans.
  * Tune sampling with `OTEL_TRACE_RATIO` (0–1). Enable `OTEL_CONSOLE_EXPORT=1` for local debugging exports.
* **Environment diagnostics**
  * `python scripts/debug_env.py` shows the source and fingerprint of every secret.

---

## Evaluation Metrics Interpretation

When you run `make eval`, metrics appear in `eval/runs/<timestamp>/metrics.json`.
They measure how well retrieval surfaces the right evidence for answer generation.

### Core Metrics

| Metric | What it Measures | Ideal Range | Notes |
|--------|------------------|------------|-------|
| **nDCG@K** | Quality of ranking — are the best chunks at the top? | 0.85–1.0 excellent | Higher is better; discounts lower ranks |
| **Recall@K** | Percentage of questions with at least one correct chunk in top-K | >=0.9 excellent | Indicates coverage |
| **MRR@K** | How early the first correct chunk appears | >=0.7 excellent | Rewards early hits |
| **HitRate@K** | Was at least one relevant chunk retrieved in the first `K` results? | >=0.9 excellent | Expressed as 0–1 in reports |
| **Precision@K** | Fraction of retrieved chunks that are relevant | Context dependent | Useful when keeping context small |

### Secondary Metrics

* **Confidence bins**: metrics are segmented into `>=0.80`, `0.70-0.79`, `0.60-0.69`, `<0.60` buckets to confirm the low-confidence path still behaves.
* **MAP** (Mean Average Precision): averages precision across ranks.
* **Coverage**: fraction of gold questions for which any relevant doc exists in the corpus.
* **Latency**: median and 95th percentile retrieval time.

### Typical Thresholds for CI

Fail the evaluation if:

* `nDCG@10` drops more than **3–5%** compared to baseline.
* `Recall@10` drops more than **5%**.
* `MRR@10` drops more than **5–10%**.

These can be tuned for production needs (e.g., stricter for tenders).

### Diagnosing Drops

* **Recall drops, nDCG stable** → content drift or chunk sizes need adjustment.
* **nDCG drops, Recall stable** → ranking issue; consider enabling a reranker.
* **Both drop** → ingestion or index regression.
* **Precision drops, Recall stable** → too many loosely relevant chunks; adjust `MAX_CONTEXT_CHUNKS` or hybrid thresholds.

Example metrics block:

```json
{
  "metrics": {
    "overall": {
      "nDCG@10": 0.86,
      "Recall@50": 0.92,
      "MRR": 0.74,
      "HitRate@5": 0.88
    },
    "confidence_bins": {
      ">=0.80": {"nDCG@10": 0.9, "Recall@50": 0.95, "MRR": 0.81, "HitRate@5": 0.95, "count": 18},
      "0.70-0.79": {"nDCG@10": 0.82, "Recall@50": 0.9, "MRR": 0.7, "HitRate@5": 0.86, "count": 6},
      "0.60-0.69": {"nDCG@10": 0.74, "Recall@50": 0.82, "MRR": 0.6, "HitRate@5": 0.78, "count": 3},
      "<0.60": {"nDCG@10": 0.65, "Recall@50": 0.7, "MRR": 0.45, "HitRate@5": 0.6, "count": 2}
    }
  }
}
```

Interpretation: strong ranking and recall overall, with slightly weaker performance in the `<0.60` bucket that warrants review.

---

## References

* [README.md](README.md) — first-time setup and Make targets
* [AGENTS.md](AGENTS.md) — architecture and error policy
* [SECURITY.md](SECURITY.md) — secrets and IAM policy
* [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — quick fixes
