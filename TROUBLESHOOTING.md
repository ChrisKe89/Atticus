# TROUBLESHOOTING — Atticus

This guide covers common setup issues, ingestion problems, and quick diagnostics for Atticus deployments.

---

## Windows Setup Issues

* **Tesseract / Ghostscript**
  * Ensure both are installed and added to the system `PATH`.
  * If OCR or PDF parsing fails, verify their paths by running `tesseract --version` and `gswin64c --version`.

* **Python Wheels for 3.12**
  * If a dependency fails to build, rerun:

    ```bash
    pip install -r requirements.txt
    ```

    to rebuild compatible wheels.

---

## PDF Parsing & Ingestion

* Prefer the **native text layer** for PDF extraction.
* OCR fallback is triggered only if no text layer is detected.
* After ingestion, verify that the number of chunks and token ranges match expectations in `logs/app.jsonl`.

Common ingestion checks:

* `.env` missing → run `python scripts/generate_env.py`.
* Unexpectedly small chunk counts → confirm `CHUNK_*` settings in `.env`.

---

## SMTP / Email Escalation

* Verify all SMTP settings in `.env`: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`, and `CONTACT_EMAIL`.
* Check network/firewall rules if emails do not send.
* Use the built‑in test:

  ```bash
  make smtp-test
  ```

---

## FastAPI / UI

* If the API fails to start:
  * Run `make lint` and `make typecheck` to catch syntax or typing errors.
  * Check logs in `logs/errors.jsonl` for stack traces.
* Confirm the UI is accessible at `http://localhost:8000/`.
  If the UI has been separated, reintroduce `make ui` and update port mapping.

---

## Index and Retrieval Issues

* **Rollback to a known-good index**:

  ```bash
  python scripts/rollback.py --manifest indices/manifest.json
  ```

* **Smoke test after rollback**:

  ```bash
  make eval
  ```

* If retrieval quality drops (low nDCG or Recall), re-run `make ingest` and re-check chunking settings.

---

## Quick Diagnostic Commands

| Action | Command |
|--------|--------|
| Check environment fingerprints | `python scripts/debug_env.py` |
| Tail live logs | `tail -f logs/app.jsonl` |
| Check errors only | `tail -f logs/errors.jsonl` |
| Full end-to-end smoke test | `make e2e` |

---

## References

* [README.md](../README.md) — installation and setup
* [OPERATIONS.md](../OPERATIONS.md) — detailed runbooks and evaluation metrics
* [SECURITY.md](../SECURITY.md) — secret handling and IAM policy examples
