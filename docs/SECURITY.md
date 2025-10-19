# SECURITY — Atticus

This guide defines security boundaries for the trusted network perimeter, secrets, email/SES, admin tokens, logging, and reporting.

---

## Trusted Network & Upstream SSO

Atticus only accepts traffic that has already passed through the enterprise SSO gateway.

- **No in-app auth** — the application never renders login forms or validates passwords/tokens.
- **Gateway enforced TLS** — require `X-Forwarded-Proto=https` for every non-loopback request.
- **Identity headers required** — deployments must forward `X-Request-Id`, `X-User-Id`, and `X-User-Email` (or equivalent) so downstream services inherit the authenticated context.
- **Network restriction** — expose ports `8000` (chat/API) and `9000` (admin) only within the trusted network ranges or through the gateway.
- **Incident escalation** — if identity headers are missing or the gateway becomes unavailable, follow the support playbook to contact the perimeter team before re-exposing services.

---

## Supported Versions

Security updates are guaranteed for the latest released minor and patch versions.
Older releases may receive fixes on a best‑effort basis only.

---

## Reporting a Vulnerability

If you discover a security issue:

1. Do not open a public GitHub issue.
2. Email the maintainers or your internal security contact with:
   - A clear description of the vulnerability and its potential impact
   - Steps to reproduce or a proof‑of‑concept
   - Affected versions and environment details

We acknowledge reports within 3 business days and coordinate a fix and disclosure timeline.

---

## Secrets Management

- Never commit secrets to source control.
- Configuration is sourced from `.env`; host env may override.
- Recommended environment keys (minimum for production):
  - `OPENAI_API_KEY`, `DATABASE_URL`
  - `EMAIL_FROM`, `EMAIL_SERVER_HOST`, `EMAIL_SERVER_PORT`, `EMAIL_SERVER_USER`, `EMAIL_SERVER_PASSWORD`
  - `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM` (fallbacks supported by the UI mailer)
  - `ADMIN_API_TOKEN`
  - `ALLOWED_ORIGINS` (lock CORS to the enterprise gateway domain list)
- Run diagnostics any time:

```bash
python scripts/debug_env.py
```

---

## Email / SES Policy (Canonical)

All outbound email and escalation are covered by this policy.

- Provider: AWS SES (region per environment)
- Identities: Use verified domains/addresses only; rotate credentials regularly
- Credentials: Environment variables only; no secrets in code or docs
  - `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`, `EMAIL_SERVER_*`
- Sandbox: For local/dev, set `EMAIL_SANDBOX=true` and relay to a non‑delivery sink (MailHog or AWS sandbox)
- Allow‑list: In lower environments, send only to allow‑listed recipients
- Auditing: Log message metadata (no PII) with `request_id`; store under `logs/` with retention
- IAM policy: Restrict `ses:FromAddress` and region

> Operational how‑to (setup, DNS verification) should link here rather than duplicate details.

---

## Admin API Token Policy

- Header: `X-Admin-Token`
- Behavior: Missing header → 401; wrong token → 403
- Storage: Use `ADMIN_API_TOKEN` env var. Do not commit tokens.
- Scope: Required for privileged admin‑only routes (e.g., queue ops, maintenance endpoints)

> Keep this the single source of truth; runbooks should reference this section.

---

## Data Privacy and Logging

- Redact PII in logs/traces; never log secret values
- App logs: `logs/app.jsonl`; error logs: `logs/errors.jsonl`
- Include `request_id` and minimal context for correlation
- Error logging intentionally omits chat payloads—only `request_id`, route, and error metadata are retained.

---

## Contributor Guidelines

- Use environment variables or a secret store (e.g. AWS Secrets Manager)
- Follow least‑privilege and data‑minimisation
- Before submitting code, run:

```bash
make lint
make typecheck
```

---

## Cross‑References

- AGENTS.md — architecture and escalation policies
- OPERATIONS.md — day‑to‑day operations and evaluation
- docs/README.md — documentation index
