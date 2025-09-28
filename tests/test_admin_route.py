from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_admin_dictionary_round_trip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_module = pytest.importorskip("atticus.config")
    config_module.reset_settings_cache()
    dictionary_path = tmp_path / "dictionary.json"
    monkeypatch.setenv("DICTIONARY_PATH", str(dictionary_path))

    api_main = pytest.importorskip("api.main")
    TestClient = pytest.importorskip("fastapi.testclient").TestClient

    client = TestClient(api_main.app)

    payload = {
        "entries": [
            {"term": "Managed print", "synonyms": ["MPS", "Print-as-a-service"]}
        ]
    }
    response = client.post("/admin/dictionary", json=payload)
    assert response.status_code == 200
    assert response.json()["entries"][0]["term"] == "Managed print"

    retrieved = client.get("/admin/dictionary")
    assert retrieved.status_code == 200
    data = retrieved.json()
    assert data["entries"]
    entry = data["entries"][0]
    assert entry["term"] == "Managed print"
    assert entry["synonyms"] == ["MPS", "Print-as-a-service"]

    raw_file = json.loads(dictionary_path.read_text(encoding="utf-8"))
    assert raw_file[0]["synonyms"] == ["MPS", "Print-as-a-service"]
