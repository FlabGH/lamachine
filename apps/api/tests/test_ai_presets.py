import pytest

from app.services.ai.presets import (
    AI_BACKEND_PRESETS,
    get_ai_backend_preset_name,
    resolve_ai_backend_preset,
)


def test_default_ai_backend_preset_is_local():
    preset = resolve_ai_backend_preset()

    assert preset.name == "local"
    assert preset.embedding_provider == "local"
    assert preset.reranker_provider == "local"
    assert preset.llm_provider == "local"


def test_mistral_jina_preset_selects_real_providers():
    preset = resolve_ai_backend_preset("mistral-jina")

    assert preset.embedding_provider == "mistral"
    assert preset.reranker_provider == "jina"
    assert preset.llm_provider == "mistral"


def test_mistral_local_rerank_keeps_local_reranker_fallback():
    preset = resolve_ai_backend_preset("mistral-local-rerank")

    assert preset.embedding_provider == "mistral"
    assert preset.reranker_provider == "local"
    assert preset.llm_provider == "mistral"


def test_ai_backend_preset_name_is_read_from_env(monkeypatch):
    monkeypatch.setenv("AI_BACKEND_PRESET", " MISTRAL-JINA ")

    assert get_ai_backend_preset_name() == "mistral-jina"


def test_unknown_ai_backend_preset_raises():
    with pytest.raises(ValueError, match="Unknown AI backend preset"):
        resolve_ai_backend_preset("unknown")


def test_expected_generic_presets_are_registered():
    assert {"local", "mistral-jina", "mistral-local-rerank"}.issubset(
        AI_BACKEND_PRESETS
    )
