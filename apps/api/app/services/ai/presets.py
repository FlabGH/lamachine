from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AIBackendPreset:
    name: str
    embedding_provider: str
    reranker_provider: str
    llm_provider: str


AI_BACKEND_PRESETS: dict[str, AIBackendPreset] = {
    "local": AIBackendPreset(
        name="local",
        embedding_provider="local",
        reranker_provider="local",
        llm_provider="local",
    ),
    "poc-mistral-jina": AIBackendPreset(
        name="poc-mistral-jina",
        embedding_provider="mistral",
        reranker_provider="jina",
        llm_provider="mistral",
    ),
    "poc-hybrid": AIBackendPreset(
        name="poc-hybrid",
        embedding_provider="mistral",
        reranker_provider="local",
        llm_provider="mistral",
    ),
}


def get_ai_backend_preset_name() -> str:
    return os.getenv("AI_BACKEND_PRESET", "local").strip().lower() or "local"


def resolve_ai_backend_preset(name: str | None = None) -> AIBackendPreset:
    preset_name = (name or get_ai_backend_preset_name()).strip().lower() or "local"
    try:
        return AI_BACKEND_PRESETS[preset_name]
    except KeyError as exc:
        known = ", ".join(sorted(AI_BACKEND_PRESETS))
        raise ValueError(f"Unknown AI backend preset: {preset_name}. Known presets: {known}") from exc
