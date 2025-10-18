from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_glossary_hits_detect_alias(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_module = pytest.importorskip("atticus.config")
    config_module.reset_settings_cache()
    dictionary_path = tmp_path / "dictionary.json"
    dictionary_path.write_text(
        json.dumps(
            [
                {
                    "term": "Managed Print Services",
                    "definition": "Enterprise subscription that manages fleets and consumables.",
                    "synonyms": ["MPS"],
                    "aliases": ["Managed Print"],
                    "units": ["fleets"],
                    "productFamilies": ["Enterprise Services"],
                }
            ],
            indent=2,
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("DICTIONARY_PATH", str(dictionary_path))
    settings = config_module.load_settings()

    glossary_module = pytest.importorskip("atticus.glossary")
    glossary_module.load_glossary_entries.cache_clear()
    entries = glossary_module.load_glossary_entries(settings)
    assert entries, "Expected glossary entries to load"

    hits = glossary_module.find_glossary_hits(
        answer="Our managed print rollout reduced fleet incidents by 12%.",
        question="How does MPS support fleet stability?",
        entries=entries,
    )
    assert len(hits) == 1
    hit = hits[0]
    assert hit.term == "Managed Print Services"
    assert hit.matched_value.lower() in {"managed print services", "managed print", "mps"}
    assert tuple(hit.aliases) == ("Managed Print",)
    assert tuple(hit.units) == ("fleets",)
    assert tuple(hit.product_families) == ("Enterprise Services",)
