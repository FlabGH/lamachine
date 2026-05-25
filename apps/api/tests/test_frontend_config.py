from app.api.config import get_frontend_config
from app.services.frontend_config import build_frontend_config


SENSITIVE_MARKERS = ("API_KEY", "SECRET", "PASSWORD", "TOKEN")


def _flatten_keys(payload: dict, prefix: str = "") -> list[str]:
    keys = []
    for key, value in payload.items():
        full_key = f"{prefix}.{key}" if prefix else key
        keys.append(full_key)
        if isinstance(value, dict):
            keys.extend(_flatten_keys(value, full_key))
        elif isinstance(value, list):
            for index, item in enumerate(value):
                if isinstance(item, dict):
                    keys.extend(_flatten_keys(item, f"{full_key}[{index}]"))
    return keys


def test_frontend_config_exposes_active_preset_from_env(monkeypatch):
    monkeypatch.setenv("AI_BACKEND_PRESET", "poc-mistral-jina")

    config = build_frontend_config()

    assert config["ai_backend_preset"] == "poc-mistral-jina"
    assert config["selected_providers"] == {
        "embedding_provider": "mistral",
        "reranker_provider": "jina",
        "llm_provider": "mistral",
    }


def test_frontend_config_preset_overrides_direct_provider_env(monkeypatch):
    monkeypatch.setenv("AI_BACKEND_PRESET", "poc-mistral-jina")
    monkeypatch.setenv("EMBEDDING_PROVIDER", "local")
    monkeypatch.setenv("RERANKER_PROVIDER", "local")
    monkeypatch.setenv("LLM_PROVIDER", "local")

    config = build_frontend_config()

    assert config["selected_providers"] == {
        "embedding_provider": "mistral",
        "reranker_provider": "jina",
        "llm_provider": "mistral",
    }


def test_frontend_config_uses_direct_provider_env_without_preset(monkeypatch):
    monkeypatch.setenv("EMBEDDING_PROVIDER", "mistral")
    monkeypatch.setenv("RERANKER_PROVIDER", "jina")
    monkeypatch.setenv("LLM_PROVIDER", "mistral")

    config = build_frontend_config()

    assert config["ai_backend_preset"] == "local"
    assert config["selected_providers"] == {
        "embedding_provider": "mistral",
        "reranker_provider": "jina",
        "llm_provider": "mistral",
    }


def test_frontend_config_lists_expected_presets():
    config = build_frontend_config()
    preset_names = {
        preset["name"]
        for preset in config["available_ai_backend_presets"]
    }

    assert {"local", "poc-mistral-jina", "poc-hybrid"}.issubset(preset_names)


def test_frontend_config_exposes_generation_defaults():
    config = build_frontend_config()

    assert config["default_generation"] == {
        "personas": ["elu", "militant", "presse"],
        "top_k": 10,
        "rerank_top_k": 5,
        "prompt_version": "note_riposte_v1",
    }


def test_frontend_config_exposes_feature_flags():
    config = build_frontend_config()

    assert config["features"] == {
        "document_text_ingestion": True,
        "document_pdf_ingestion": True,
        "search": True,
        "generate_note": True,
        "traceability": True,
        "preset_selection": False,
    }


def test_frontend_config_does_not_expose_secret_keys():
    config = build_frontend_config()
    flattened_keys = _flatten_keys(config)

    assert not any(
        marker in key.upper()
        for key in flattened_keys
        for marker in SENSITIVE_MARKERS
    )


def test_frontend_config_endpoint_returns_service_payload(monkeypatch):
    monkeypatch.setenv("AI_BACKEND_PRESET", "poc-hybrid")

    assert get_frontend_config() == build_frontend_config()
