from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class ProviderError(Exception):
    """Base exception for provider/adapter errors."""


class ProviderTimeout(ProviderError):
    """Raised when a provider call times out."""


class ProviderRetryError(ProviderError):
    """Raised when retries for a provider call are exhausted."""


@dataclass(frozen=True)
class LLMMessage:
    role: str  # system | user | assistant
    content: str


@dataclass(frozen=True)
class LLMResult:
    text: str
    provider: str
    model: str
    raw: dict[str, Any] | None = None


@dataclass(frozen=True)
class EmbeddingResult:
    vectors: list[list[float]]
    provider: str
    model: str
    dimension: int
    raw: dict[str, Any] | None = None


@dataclass(frozen=True)
class RerankCandidate:
    id: str
    text: str
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class RerankResult:
    id: str
    score: float
    rank: int


class LLMClient(Protocol):
    provider: str
    model: str

    async def generate(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> LLMResult:
        ...


class EmbeddingClient(Protocol):
    provider: str
    model: str
    dimension: int

    async def embed_texts(
        self,
        texts: list[str],
        *,
        metadata: dict[str, Any] | None = None,
    ) -> EmbeddingResult:
        ...


class RerankerClient(Protocol):
    provider: str
    model: str

    async def rerank(
        self,
        query: str,
        candidates: list[RerankCandidate],
        *,
        top_k: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[RerankResult]:
        ...
