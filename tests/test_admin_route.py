from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest


def test_admin_dictionary_round_trip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_module = pytest.importorskip("atticus.config")
    config_module.reset_settings_cache()
    dictionary_path = tmp_path / "dictionary.json"
    monkeypatch.setenv("DICTIONARY_PATH", str(dictionary_path))
    monkeypatch.setenv("ADMIN_API_TOKEN", "test-admin-token")
    settings = config_module.load_settings()
    assert settings.dictionary_path == dictionary_path

    api_main = pytest.importorskip("api.main")
    TestClient = pytest.importorskip("fastapi.testclient").TestClient

    with TestClient(api_main.app) as client:
        payload = {
            "entries": [{"term": "Managed print", "synonyms": ["MPS", "Print-as-a-service"]}]
        }
        response = client.post(
            "/admin/dictionary", json=payload, headers={"X-Admin-Token": "test-admin-token"}
        )
        assert response.status_code == 200
        assert response.json()["entries"][0]["term"] == "Managed print"

        retrieved = client.get("/admin/dictionary", headers={"X-Admin-Token": "test-admin-token"})
        assert retrieved.status_code == 200
        data = retrieved.json()
        assert data["entries"]
        entry = data["entries"][0]
        assert entry["term"] == "Managed print"
        assert entry["synonyms"] == ["MPS", "Print-as-a-service"]

    raw_file = json.loads(dictionary_path.read_text(encoding="utf-8"))
    assert raw_file[0]["synonyms"] == ["MPS", "Print-as-a-service"]


def test_admin_dictionary_requires_token(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_module = pytest.importorskip("atticus.config")
    config_module.reset_settings_cache()
    dictionary_path = tmp_path / "dictionary.json"
    monkeypatch.setenv("DICTIONARY_PATH", str(dictionary_path))
    monkeypatch.setenv("ADMIN_API_TOKEN", "test-admin-token")
    settings = config_module.load_settings()
    assert settings.dictionary_path == dictionary_path

    api_main = pytest.importorskip("api.main")
    TestClient = pytest.importorskip("fastapi.testclient").TestClient

    with TestClient(api_main.app) as client:
        response = client.get("/admin/dictionary")
        assert response.status_code == 401
        data = response.json()
        assert data["error"] == "unauthorized"
        assert data["request_id"]


def test_admin_dictionary_rejects_invalid_token(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_module = pytest.importorskip("atticus.config")
    config_module.reset_settings_cache()
    dictionary_path = tmp_path / "dictionary.json"
    monkeypatch.setenv("DICTIONARY_PATH", str(dictionary_path))
    monkeypatch.setenv("ADMIN_API_TOKEN", "test-admin-token")
    settings = config_module.load_settings()
    assert settings.dictionary_path == dictionary_path

    api_main = pytest.importorskip("api.main")
    TestClient = pytest.importorskip("fastapi.testclient").TestClient

    with TestClient(api_main.app) as client:
        response = client.get("/admin/dictionary", headers={"X-Admin-Token": "wrong-token"})
        assert response.status_code == 403
        data = response.json()
        assert data["error"] == "forbidden"
        assert data["detail"] == "Invalid admin token."
        assert data["request_id"]


def test_admin_eval_seeds_round_trip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_module = pytest.importorskip("atticus.config")
    config_module.reset_settings_cache()
    gold_path = tmp_path / "gold.csv"
    monkeypatch.setenv("GOLD_SET_PATH", str(gold_path))
    monkeypatch.setenv("ADMIN_API_TOKEN", "test-admin-token")
    settings = config_module.load_settings()
    assert settings.gold_set_path == gold_path

    api_main = pytest.importorskip("api.main")
    TestClient = pytest.importorskip("fastapi.testclient").TestClient

    payload = {
        "seeds": [
            {
                "question": "What is the warm-up time of the Apeos C7070?",
                "relevantDocuments": ["content/ced/apeos-c7070.pdf"],
                "expectedAnswer": "30 seconds or less",
                "notes": "Verify against 2025 refresh",
            }
        ]
    }

    with TestClient(api_main.app) as client:
        response = client.post(
            "/admin/eval-seeds",
            json=payload,
            headers={"X-Admin-Token": "test-admin-token"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["seeds"][0]["question"] == payload["seeds"][0]["question"]

        retrieved = client.get(
            "/admin/eval-seeds",
            headers={"X-Admin-Token": "test-admin-token"},
        )
        assert retrieved.status_code == 200
        data = retrieved.json()
        assert len(data["seeds"]) == 1
        seed = data["seeds"][0]
        documents = seed.get("relevantDocuments") or seed.get("relevant_documents")
        assert documents == ["content/ced/apeos-c7070.pdf"]
        expected_answer = seed.get("expectedAnswer") or seed.get("expected_answer")
        assert expected_answer == "30 seconds or less"

    with gold_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    assert rows[0]["question"] == "What is the warm-up time of the Apeos C7070?"
    assert rows[0]["relevant_documents"] == "content/ced/apeos-c7070.pdf"


def test_admin_eval_seeds_rejects_blank_question(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_module = pytest.importorskip("atticus.config")
    config_module.reset_settings_cache()
    gold_path = tmp_path / "gold.csv"
    monkeypatch.setenv("GOLD_SET_PATH", str(gold_path))
    monkeypatch.setenv("ADMIN_API_TOKEN", "test-admin-token")
    settings = config_module.load_settings()
    assert settings.gold_set_path == gold_path

    api_main = pytest.importorskip("api.main")
    TestClient = pytest.importorskip("fastapi.testclient").TestClient

    with TestClient(api_main.app) as client:
        response = client.post(
            "/admin/eval-seeds",
            json={"seeds": [{"question": "   ", "relevantDocuments": []}]},
            headers={"X-Admin-Token": "test-admin-token"},
        )
        assert response.status_code == 422
        detail = response.json()
        payload = detail.get("detail") if isinstance(detail, dict) else None
        if isinstance(payload, list) and payload and isinstance(payload[0], dict):
            assert str(payload[0].get("msg", "")).startswith(
                "Value error, Question must not be empty"
            )
        else:
            assert isinstance(payload, str)
            assert payload.endswith("Question must not be empty")
