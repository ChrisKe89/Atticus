# Security Policy

## Supported Versions

We support security updates on the latest released minor/patch versions. Older releases may receive fixes on a best-effort basis.

## Reporting a Vulnerability

- Please email the maintainers or your internal security contact with:
  - A clear description of the issue and potential impact
  - Steps to reproduce and any proof-of-concept
  - Affected versions and environment details
- Do not open a public issue with sensitive details.

We will acknowledge receipt within 3 business days and coordinate a fix and disclosure timeline.

## Guidance for Contributors

- Do not commit secrets. Use environment variables and secret stores.
- Follow least-privilege and data minimization principles.
- Redact PII in logs and traces. See `atticus.logging` and AGENTS.md §6 for details.

