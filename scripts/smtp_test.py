"""Manual SMTP smoke test used by `make smtp-test`."""

from __future__ import annotations

import sys

try:
    from atticus.notify.mailer import send_escalation
except Exception as exc:  # pragma: no cover - import is optional for devs
    IMPORT_ERROR = exc
    send_escalation = None
else:
    IMPORT_ERROR = None


def main() -> None:
    if send_escalation is None:
        print("SMTP mailer is unavailable: atticus.notify.mailer could not be imported.")
        if IMPORT_ERROR:
            print(f"Reason: {IMPORT_ERROR}")
        sys.exit(1)

    send_escalation("Atticus SMTP test", "This is a test from make smtp-test")
    print("smtp ok")


if __name__ == "__main__":
    main()
