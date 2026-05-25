from __future__ import annotations

from typing import Any

from app.api.documentary import GenerateNoteRequest
from app.services.ai.presets import AI_BACKEND_PRESETS, resolve_ai_backend_preset


def build_frontend_config() -> dict[str, Any]:
    active_preset = resolve_ai_backend_preset()
    default_generation = GenerateNoteRequest(
        query="",
        index_version_id="00000000-0000-0000-0000-000000000000",
    )

    return {
        "ai_backend_preset": active_preset.name,
        "available_ai_backend_presets": [
            {
                "name": preset.name,
                "embedding_provider": preset.embedding_provider,
                "reranker_provider": preset.reranker_provider,
                "llm_provider": preset.llm_provider,
            }
            for preset in AI_BACKEND_PRESETS.values()
        ],
        "selected_providers": {
            "embedding_provider": active_preset.embedding_provider,
            "reranker_provider": active_preset.reranker_provider,
            "llm_provider": active_preset.llm_provider,
        },
        "default_generation": {
            "personas": [persona.value for persona in default_generation.personas],
            "top_k": default_generation.top_k,
            "rerank_top_k": default_generation.rerank_top_k,
            "prompt_version": default_generation.prompt_version,
        },
        "features": {
            "document_text_ingestion": True,
            "document_pdf_ingestion": True,
            "search": True,
            "generate_note": True,
            "traceability": True,
            "preset_selection": False,
        },
    }
