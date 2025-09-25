# Infra Overview

This directory centralises deployment assets for Atticus. The current scope captures configuration for:

* **Docker Compose profiles** for the API, UI, and evaluation services.
* **OTel collector integration** — configure `OTEL_EXPORTER_OTLP_ENDPOINT` in `.env` or environment.
* **NGINX reverse proxy stubs** for the MCP gateway and UI assets.

## Next Steps

* Add k8s manifests for production rollouts.
* Include Terraform for managed object storage and nightly index backups.
