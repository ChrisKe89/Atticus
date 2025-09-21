from __future__ import annotations

from fastapi.testclient import TestClient
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.main import app  # noqa: E402


def main() -> None:
    with TestClient(app) as client:
        res = client.get("/health")
        print("status:", res.status_code)
        print("json:", res.json())


if __name__ == "__main__":
    main()
