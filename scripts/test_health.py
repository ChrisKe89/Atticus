from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for candidate in (SRC, ROOT):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

from api.main import app  # noqa: E402


def main() -> None:
    with TestClient(app) as client:
        res = client.get("/health")
        print("status:", res.status_code)
        print("json:", res.json())


if __name__ == "__main__":
    main()
