# ADR 0001: Core Architecture and Observability Foundations

## Status

Accepted — 2025-09-24

## Context

Atticus is a Retrieval-Augmented Generation (RAG) assistant serving Sales and Service teams. We require:

* Reliable ingestion and retrieval pipelines with auditable results.
* A consistent escalation workflow with structured logs and traceability.
* End-to-end observability compliant with the Atticus AGENTS specification, including OpenTelemetry traces and structured logging.

## Decision

1. **Adopt the layered API → Service → Data pattern.** Routes stay thin while services coordinate retrieval, generation, and escalation logic.
2. **Persist escalations in dual logs (JSONL + CSV) and emit SES-ready email payloads** that match the mandated schema. AE identifiers begin at `AE100` and are monotonic.
3. **Standardise on OpenTelemetry for tracing.** Each API request starts a span, and trace/span identifiers are injected into
   every log entry. Spans are exported via OTLP and can be inspected locally via console export.
4. **Codify observability tooling in Make targets and scripts** so CI/CD can run ingestion → evaluation → smoke → UI ping
   flows without manual intervention.

## Consequences

* Logs, spans, and escalation outputs now share a request identifier, simplifying audits.
* Deployments must provide an OTLP collector endpoint (defaults to `http://localhost:4318/v1/traces`).
* Any future service changes must record new architectural decisions under `adr/` to keep the history authoritative.
* Local developers gain a one-command path (`make e2e`) to exercise the entire workflow, enforcing quality gates.
