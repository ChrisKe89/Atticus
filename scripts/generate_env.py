#!/usr/bin/env python3
"""Create or refresh the repository .env file.

Usage examples::

    python scripts/generate_env.py            # creates .env if missing
    python scripts/generate_env.py --force    # overwrite existing .env
    python scripts/generate_env.py --ignore-env   # ignore host env vars when writing
"""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path


def _fingerprint(value: str | None) -> str | None:
    if not value:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


DEFAULTS = {
    "OPENAI_MODEL": "gpt-4.1",
    "OPENAI_API_KEY": "",
    "EMBED_MODEL": "text-embedding-3-large",
    "EMBEDDING_MODEL_VERSION": "text-embedding-3-large@2025-01-15",
    "GEN_MODEL": "gpt-4.1",
    "CONFIDENCE_THRESHOLD": "0.70",
    "CHUNK_TARGET_TOKENS": "512",
    "CHUNK_MIN_TOKENS": "256",
    "CHUNK_OVERLAP_TOKENS": "100",
    "MAX_CONTEXT_CHUNKS": "10",
    "LOG_LEVEL": "INFO",
    "LOG_VERBOSE": "0",
    "LOG_TRACE": "0",
    "TIMEZONE": "UTC",
    "EVAL_REGRESSION_THRESHOLD": "3.0",
    "CONTENT_DIR": "./content",
    "CONTACT_EMAIL": "atticus-contact@agentk.fyi",
    "SMTP_HOST": "email-smtp.ap-southeast-2.amazonaws.com",
    "SMTP_PORT": "587",
    "SMTP_USER": "atticus-escalations",
    "SMTP_PASS": "Pay641-Prove-Possible-stop-Cry",
    "SMTP_FROM": "atticus-escalations@agentk.fyi",
    "SMTP_TO": "atticus-technical-support@agentk.fyi",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a .env file for Atticus")
    parser.add_argument("--force", action="store_true", help="overwrite an existing .env file")
    parser.add_argument(
        "--ignore-env",
        action="store_true",
        help="ignore host environment variables when populating values",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    env_path = root / ".env"

    if env_path.exists() and not args.force:
        print(f"[generate_env] .env already exists at {env_path}. Use --force to overwrite.")
        return 0

    if args.ignore_env:
        print("[generate_env] Ignoring host environment variables; writing defaults.")

    lines = []
    used_openai_key: str | None = None
    for k, v in DEFAULTS.items():
        if args.ignore_env:
            val = v
        else:
            val = os.environ.get(k, v)
        if isinstance(val, str):
            val = val.strip()
        if k == "OPENAI_API_KEY":
            used_openai_key = val
        lines.append(f"{k}={val}")

    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[generate_env] Wrote {env_path}")
    if used_openai_key:
        source = (
            "environment" if not args.ignore_env and "OPENAI_API_KEY" in os.environ else "defaults"
        )
        fingerprint = _fingerprint(used_openai_key) or "none"
        print(f"[generate_env] OPENAI_API_KEY resolved from {source} (fingerprint={fingerprint})")
    else:
        print(
            "[generate_env] Note: OPENAI_API_KEY is empty. Set it via environment before running, e.g.\n"
            "  PowerShell:  $env:OPENAI_API_KEY='sk-...' ; python scripts/generate_env.py --force\n"
            "  Bash:        OPENAI_API_KEY='sk-...' python scripts/generate_env.py --force"
        )
    if (
        not args.ignore_env
        and "OPENAI_API_KEY" in os.environ
        and os.environ.get("OPENAI_API_KEY", "").strip() != (used_openai_key or "")
    ):
        print(
            "[generate_env] Warning: host OPENAI_API_KEY differs from written value. Run with --ignore-env to bypass host overrides."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
