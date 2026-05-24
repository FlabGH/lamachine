from __future__ import annotations

from typing import Optional

from app.services.ai.embedding_adapters import HashEmbeddingClient
from app.services.ai.reranker_adapters import LexicalOverlapReranker
from app.services.ai.llm_adapters import ExtractiveNoteLLMClient


def get_embedding_client(provider: Optional[str] = None, model: Optional[str] = None):
    """Return an EmbeddingClient instance.

    Minimal factory for Step 1: always return the local fallback.
    """
    return HashEmbeddingClient()


def get_reranker_client(provider: Optional[str] = None, model: Optional[str] = None):
    """Return a RerankerClient instance. Minimal local fallback."""
    return LexicalOverlapReranker()


def get_llm_client(provider: Optional[str] = None, model: Optional[str] = None):
    """Return an LLMClient instance. Minimal local fallback."""
    return ExtractiveNoteLLMClient()
