from __future__ import annotations

import pytest

from retriever.prompts import available_versions, get_prompt_template


def test_get_prompt_template_known_version() -> None:
    version = available_versions()[0]
    template = get_prompt_template(version)
    rendered = template.render_user(prompt="Hello?", context="Some context")
    assert "Hello?" in rendered
    assert "Some context" in rendered


def test_get_prompt_template_unknown_version() -> None:
    with pytest.raises(KeyError):
        get_prompt_template("missing-version")
