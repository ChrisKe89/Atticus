# SECURITY — Atticus

This guide describes how to handle secrets, protect data, and report vulnerabilities when operating Atticus.

---

## Supported Versions

Security updates are guaranteed for the latest released minor and patch versions.
Older releases may receive fixes on a best‑effort basis only.

---

## Reporting a Vulnerability

If you discover a security issue:

1. **Do not** open a public GitHub issue.
2. Email the maintainers or your internal security contact with:
   * A clear description of the vulnerability and its potential impact.
   * Steps to reproduce or a proof‑of‑concept.
   * Affected versions and environment details.

We acknowledge reports within **3 business days** and coordinate a fix and disclosure timeline.

---

## Secrets Management

* **Never commit secrets** to source control.
* All configuration is read from `.env`. Host environment variables may override unless you set `ATTICUS_ENV_PRIORITY=env`.
* Recommended environment keys (minimum for production):
  - `OPENAI_API_KEY`
  - `CONTACT_EMAIL`
  - `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`
* Run diagnostics at any time:
  ```bash
  python scripts/debug_env.py
  ```
  This shows the source of each secret and a fingerprint for quick audits.

---

## Email Security (Amazon SES)

* Use **SES SMTP credentials** (not IAM access keys) for mail sending.
* The `SMTP_FROM` address must be a **verified SES identity** in the same AWS region.
* If your SES account is in **sandbox mode**, all recipients must be verified until production access is granted.
* Apply an IAM policy that **restricts sending** to approved addresses and your region only. Example:
  ```json
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": "ses:SendRawEmail",
        "Resource": "*",
        "Condition": {
          "StringEquals": {
            "ses:FromAddress": "atticus-escalations@yourdomain",
            "aws:RequestedRegion": "ap-southeast-2"
          }
        }
      }
    ]
  }
  ```
  ::: tip
  Update the address and region to match your verified SES identity (e.g. "us-east-1").
  :::

---

## Data Privacy and Logging

* **Redact PII** (personally identifiable information) in all logs and traces.
* The built‑in loggers `logs/app.jsonl` and `logs/errors.jsonl` already exclude known secret keys.
* Preserve stack traces for debugging but never log actual secret values.

---

## Contributor Guidelines

* Use environment variables and secret stores (e.g. AWS Secrets Manager) instead of hard‑coding credentials.
* Follow least‑privilege and data‑minimisation principles when accessing data sources.
* Before submitting code, run:
  ```bash
  make fmt
  make lint
  make type
  ```
  to ensure nothing leaks into commits.

---

## Cross-References

* [AGENTS.md](AGENTS.md) — system architecture and escalation policies.
* [README.md](README.md) — quick-start and environment setup.
* [OPERATIONS.md](OPERATIONS.md) — day-to-day operations and evaluation metrics.
