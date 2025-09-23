# TROUBLESHOOTING.md

## Windows setup
- Ensure Tesseract and Ghostscript are installed and on PATH when needed for PDFs.
- For Python 3.12 wheels, re-run `pip install -r requirements.txt` if build deps change.

## PDF parsing
- Prefer text layer extraction; fall back to OCR selectively.
- Validate chunk counts and token ranges after ingestion.

## Common issues
- `.env` missing → run `python scripts/generate_env.py`.
- SMTP failures → check HOST/PORT/USER/PASS and firewall rules.
