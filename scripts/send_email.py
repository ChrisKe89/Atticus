#!/usr/bin/env python3
"""Send an escalation email using SMTP with retry/backoff."""

from __future__ import annotations

import argparse
import json
import time
from collections.abc import Sequence

from atticus.config import load_settings
from atticus.notify.mailer import send_escalation


def main() -> int:
    parser = argparse.ArgumentParser(description="Send an escalation email payload")
    parser.add_argument("--subject", required=True, help="Email subject")
    parser.add_argument("--body", required=True, help="Email body text")
    parser.add_argument("--to", nargs="*", default=[], help="Recipients")
    parser.add_argument("--cc", nargs="*", default=[], help="CC recipients")
    parser.add_argument("--retries", type=int, default=3, help="Retry attempts on failure")
    parser.add_argument("--backoff", type=float, default=1.5, help="Exponential backoff multiplier")
    args = parser.parse_args()

    settings = load_settings()
    attempt = 0
    while True:
        attempt += 1
        try:
            recipients: Sequence[str]
            if args.to:
                recipients = args.to
            elif settings.smtp_to:
                recipients = [settings.smtp_to]
            elif settings.contact_email:
                recipients = [settings.contact_email]
            else:
                recipients = []

            if args.cc:
                cc_list: Sequence[str] = args.cc
            elif settings.contact_email:
                cc_list = [settings.contact_email]
            else:
                cc_list = []
            result = send_escalation(
                subject=args.subject,
                body=args.body,
                to=recipients,
                cc=cc_list,
            )
            if result is not None:
                print(json.dumps(result, indent=2))
            return 0
        except Exception:  # pragma: no cover - network path
            if attempt >= max(1, args.retries):
                raise
            time.sleep(args.backoff**attempt)


if __name__ == "__main__":
    raise SystemExit(main())
