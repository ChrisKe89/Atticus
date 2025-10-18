#!/usr/bin/env python3
"""Poll an HTTP endpoint until it returns a healthy status code."""

from __future__ import annotations

import argparse
import sys
import time
from urllib.request import Request, urlopen


def wait_for_health(url: str, timeout: int, interval: float) -> int:
    deadline = time.time() + timeout
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            req = Request(url, method="GET")
            with urlopen(req, timeout=interval) as response:  # noqa: S310
                if 200 <= response.status < 300:
                    return 0
        except Exception as exc:  # pragma: no cover - network errors in CI only
            last_error = exc
        time.sleep(interval)
    if last_error:
        print(f"Health check failed for {url}: {last_error}", file=sys.stderr)
    else:
        print(f"Health check timed out after {timeout}s for {url}", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Wait for an HTTP endpoint to report healthy")
    parser.add_argument("--url", required=True, help="Health check URL")
    parser.add_argument("--timeout", type=int, default=60, help="Maximum wait time in seconds")
    parser.add_argument("--interval", type=float, default=2.0, help="Polling interval in seconds")
    args = parser.parse_args()
    return wait_for_health(args.url, args.timeout, args.interval)


if __name__ == "__main__":
    sys.exit(main())
