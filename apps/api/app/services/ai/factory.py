from __future__ import annotations

import os
from typing import Optional

from app.services.ai.embedding_adapters import HashEmbeddingClient, MistralEmbeddingClient
from app.services.ai.llm_adapters import ExtractiveNoteLLMClient, MistralLLMClient
from app.services.ai.ocr_adapters import MistralOcrClient, NoopOcrClient
from app.services.ai.presets import resolve_ai_backend_preset
from app.services.ai.reranker_adapters import JinaRerankerClient, LexicalOverlapReranker


def _normalize_provider(provider: Optional[str]) -> str:
    return (provider or "").strip().lower()


def _provider_from_config(
    provider: Optional[str],
    *,
    env_var: str,
    preset_field: str,
) -> str:
    explicit_provider = _normalize_provider(provider)
    if explicit_provider:
        return explicit_provider

    preset_name = os.getenv("AI_BACKEND_PRESET")
    if preset_name and preset_name.strip():
        return getattr(resolve_ai_backend_preset(preset_name), preset_field)

    env_provider = _normalize_provider(os.getenv(env_var))
    if env_provider:
        return env_provider

    return getattr(resolve_ai_backend_preset(), preset_field)


def get_embedding_client(provider: Optional[str] = None, model: Optional[str] = None):
    """Return an EmbeddingClient instance.

    Minimal factory for Step 1 and 2: choose provider from config, fallback local.
    """
    provider = _provider_from_config(
        provider,
        env_var="EMBEDDING_PROVIDER",
        preset_field="embedding_provider",
    )

    if provider == "local":
        return HashEmbeddingClient()

    if provider == "mistral":
        return MistralEmbeddingClient()

    raise ValueError(f"Unknown embedding provider: {provider}")


def get_reranker_client(provider: Optional[str] = None, model: Optional[str] = None):
    """Return a RerankerClient instance. Minimal local fallback."""
    provider = _provider_from_config(
        provider,
        env_var="RERANKER_PROVIDER",
        preset_field="reranker_provider",
    )

    if provider == "local":
        return LexicalOverlapReranker()

    if provider == "jina":
        return JinaRerankerClient(model=model)

    raise ValueError(f"Unknown reranker provider: {provider}")


def get_llm_client(provider: Optional[str] = None, model: Optional[str] = None):
    """Return an LLMClient instance. Minimal local fallback."""
    provider = _provider_from_config(
        provider,
        env_var="LLM_PROVIDER",
        preset_field="llm_provider",
    )

    if provider == "local":
        return ExtractiveNoteLLMClient()

    if provider == "mistral":
        return MistralLLMClient(model=model)

    raise ValueError(f"Unknown LLM provider: {provider}")


def get_ocr_client(provider: Optional[str] = None, model: Optional[str] = None):
    """Return an OcrClient instance. OCR is disabled unless explicitly configured."""
    provider = _normalize_provider(provider or os.getenv("OCR_PROVIDER"))

    if not provider or provider in {"disabled", "noop", "local"}:
        return NoopOcrClient()

    if provider == "mistral":
        return MistralOcrClient(model=model)

    raise ValueError(f"Unknown OCR provider: {provider}")
