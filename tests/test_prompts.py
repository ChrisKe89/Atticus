from __future__ import annotations

from pathlib import Path

import pytest

from atticus.prompts import PromptService


def test_prompt_service_loads_and_hot_reloads(tmp_path: Path) -> None:
    store = tmp_path / "prompts.json"
    store.write_text('{"rag": "system prompt"}\n', encoding="utf-8")
    service = PromptService(store)

    assert service.get_prompt("rag") == "system prompt"
    assert service.available_prompts() == ["rag"]

    store.write_text('{"rag": "updated", "doc": "document prompt"}\n', encoding="utf-8")
    assert service.get_prompt("doc") == "document prompt"
    assert sorted(service.available_prompts()) == ["doc", "rag"]

    with pytest.raises(KeyError):
        service.get_prompt("missing")
