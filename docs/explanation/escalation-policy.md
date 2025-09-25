# Escalation vs. Refusal Policy

Atticus blends retrieval and generation confidence to decide whether to answer,
escalate, or refuse. This policy guides both automated behaviour and the human
teams who monitor escalations.

## Confidence thresholds

| Confidence | Behaviour | Notes |
|------------|-----------|-------|
| `≥ 0.85`   | Answer    | Normal response with citations. Log `escalate=false`. |
| `0.70 – 0.84` | Answer + caution | Include a caveat sentence ("Based on available sources…") and highlight key sources. |
| `< 0.70`   | Partial answer + escalation | Return HTTP `206 Partial`, trigger SES escalation email, and append `escalate=true` to logs. |

Escalation emails include the request, retrieved sources, and `request_id` so
Sales Operations can trace the incident.

## Refusal categories

Refuse immediately (HTTP `403`) when a request matches any forbidden category:

- **Disallowed content** — personal data, credentials, or competitive intelligence.
- **Policy conflicts** — requests to fabricate quotes, pricing, or contractual commitments.
- **System maintenance** — ingest/index commands when the environment is in read-only mode (`settings.read_only`).

The response uses the shared JSON schema with `error="refused_request"`,
`detail` explaining why, and `request_id` for auditing. These events are logged
with severity `WARNING`.

## Human escalation workflow

1. SES routes escalations to `CONTACT_EMAIL` plus the team distribution lists
   defined in `.env` (`TEAM_EMAIL_*`).
2. The email subject includes the `request_id` so it can be searched in
   `logs/app.jsonl`.
3. Sales Operations triages within one business hour, looping in domain experts
   when necessary. Actions and resolutions are recorded in the CRM ticket linked
   in the escalation email body.
4. When the corpus or prompt needs improvement, create a task in `TODO.md` and
   capture the follow-up in `ToDo-Complete.md` once resolved.

## Monitoring & alerts

- Metrics recorder emits `escalations.total` and `escalations.by_category` to
  `logs/metrics/metrics.csv`.
- An alert triggers if escalation rate exceeds 10% over a rolling 24-hour
  window. Operators receive a Slack notification in `#atticus-escalations`.
- Use the `/admin/sessions` view to correlate escalations with the original chat
  transcript and retrieved sources.
