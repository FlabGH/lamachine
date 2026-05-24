from __future__ import annotations

import os
from typing import Optional

from app.services.ai.embedding_adapters import HashEmbeddingClient
from app.services.ai.llm_adapters import ExtractiveNoteLLMClient
from app.services.ai.reranker_adapters import LexicalOverlapReranker


def _normalize_provider(provider: Optional[str]) -> str:
    return (provider or "").strip().lower()


def get_embedding_client(provider: Optional[str] = None, model: Optional[str] = None):
    """Return an EmbeddingClient instance.

    Minimal factory for Step 1 and 2: choose provider from config, fallback local.
    """
    provider = _normalize_provider(provider) or os.getenv("EMBEDDING_PROVIDER", "local").lower()

    if provider == "local":
        return HashEmbeddingClient()

    raise ValueError(f"Unknown embedding provider: {provider}")


def get_reranker_client(provider: Optional[str] = None, model: Optional[str] = None):
    """Return a RerankerClient instance. Minimal local fallback."""
    provider = _normalize_provider(provider) or os.getenv("RERANKER_PROVIDER", "local").lower()

    if provider == "local":
        return LexicalOverlapReranker()

    raise ValueError(f"Unknown reranker provider: {provider}")


def get_llm_client(provider: Optional[str] = None, model: Optional[str] = None):
    """Return an LLMClient instance. Minimal local fallback."""
    provider = _normalize_provider(provider) or os.getenv("LLM_PROVIDER", "local").lower()

    if provider == "local":
        return ExtractiveNoteLLMClient()

    raise ValueError(f"Unknown LLM provider: {provider}")
