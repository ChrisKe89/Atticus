import pytest

from retriever.models import extract_models, load_model_catalog
from retriever.resolver import resolve_models


@pytest.fixture(scope="module")
def catalog():
    return load_model_catalog()


def test_extract_models_direct_hit(catalog):
    result = extract_models("Can the Apeos C7070 handle heavy cardstock?", catalog=catalog)
    assert "Apeos C7070" in result.models
    assert "C7070" in result.families
    assert result.confidence > 0.8


def test_extract_models_alias_hit(catalog):
    result = extract_models("Does the 6580 support stapling?", catalog=catalog)
    assert "Apeos C6580" in result.models
    assert "C8180" in result.families
    assert result.confidence >= 0.6


def test_extract_models_none_requires_clarification(catalog):
    result = extract_models("How do I replace the toner cartridge?", catalog=catalog)
    assert not result.models
    assert not result.families
    assert result.confidence == 0


def test_resolve_models_explicit_selection(catalog):
    resolution = resolve_models(
        question="ignored when models are explicit",
        requested_models=["Apeos C4570", "Apeos C6580"],
        catalog=catalog,
    )
    assert not resolution.needs_clarification
    assert {scope.family_id for scope in resolution.scopes} == {"C7070", "C8180"}
    assert {scope.model for scope in resolution.scopes} == {"Apeos C4570", "Apeos C6580"}


def test_resolve_models_requests_clarification(monkeypatch, catalog):
    resolution = resolve_models(
        "Tell me about the printer", catalog=catalog, clarification_threshold=0.9
    )
    assert resolution.needs_clarification
    assert resolution.scopes == []
    assert {option.id for option in resolution.clarification_options} >= {"C7070", "C8180"}
