#!/usr/bin/env python3
"""
generate_env.py - Create a .env file for Atticus with sensible defaults.

Usage:
    python scripts/generate_env.py            # creates .env if missing
    python scripts/generate_env.py --force    # overwrite existing .env
"""

import os
import sys
from pathlib import Path

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
    "CONTACT_EMAIL": "",
    "SMTP_HOST": "",
    "SMTP_PORT": "587",
    "SMTP_USER": "",
    "SMTP_PASS": "",
    "SMTP_FROM": "",
    "SMTP_TO": "",
}


def main():
    root = Path(__file__).resolve().parents[1]
    env_path = root / ".env"
    force = "--force" in sys.argv

    if env_path.exists() and not force:
        print(f"[generate_env] .env already exists at {env_path}. Use --force to overwrite.")
        return 0

    # Load existing values from environment to allow CI overrides
    lines = []
    used_openai_key: str | None = None
    for k, v in DEFAULTS.items():
        val = os.environ.get(k, v)
        if isinstance(val, str):
            val = val.strip()
        if k == "OPENAI_API_KEY":
            used_openai_key = val
        lines.append(f"{k}={val}")

    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[generate_env] Wrote {env_path}")
    if not used_openai_key:
        print(
            "[generate_env] Note: OPENAI_API_KEY is empty. Set it via environment before running, e.g.\n"
            "  PowerShell:  $env:OPENAI_API_KEY='sk-...' ; python scripts/generate_env.py --force\n"
            "  Bash:        OPENAI_API_KEY='sk-...' python scripts/generate_env.py --force"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
