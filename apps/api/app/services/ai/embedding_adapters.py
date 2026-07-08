from __future__ import annotations

import hashlib
import math
import os
from typing import Any

import httpx

from app.services.ai.clients import EmbeddingResult


class HashEmbeddingClient:
    provider = "local"
    model = "hash-embedding-v1"
    dimension = 384

    async def embed_texts(
        self,
        texts: list[str],
        *,
        metadata: dict[str, Any] | None = None,
    ) -> EmbeddingResult:
        vectors = [self._embed(text) for text in texts]
        return EmbeddingResult(
            vectors=vectors,
            provider=self.provider,
            model=self.model,
            dimension=self.dimension,
            raw={"adapter": "deterministic_hash"},
        )

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        tokens = text.lower().split()

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            idx = int.from_bytes(digest[:4], "big") % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[idx] += sign

        norm = math.sqrt(sum(x * x for x in vector)) or 1.0
        return [x / norm for x in vector]


class MistralEmbeddingClient:
    provider = "mistral"
    model = "mistral-embed"

    def __init__(self) -> None:
        env_dimension = os.getenv("MISTRAL_EMBED_DIMENSION", "").strip()
        if env_dimension:
            self.dimension = int(env_dimension)
            self._dimension_from_config = True
        else:
            self.dimension = 1024
            self._dimension_from_config = False

        if self.dimension <= 0:
            raise ValueError("MISTRAL_EMBED_DIMENSION must be a positive integer")

    async def embed_texts(
        self,
        texts: list[str],
        *,
        metadata: dict[str, Any] | None = None,
    ) -> EmbeddingResult:
        api_url = os.getenv("MISTRAL_EMBED_API_URL")
        if not api_url:
            raise ValueError("MISTRAL_EMBED_API_URL must be configured for mistral embeddings")

        api_key = os.getenv("MISTRAL_EMBED_API_KEY", "")
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        payload = {
            "model": self.model,
            "input": texts,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(api_url, json=payload, headers=headers)
            response.raise_for_status()
            body = response.json()

        data = body.get("data")
        if not isinstance(data, list) or not data:
            raise ValueError("Invalid response from Mistral embeddings provider")

        vectors = [item.get("embedding") for item in data]
        if any(vec is None for vec in vectors):
            raise ValueError("Mistral embeddings response is missing embedding vectors")

        dimension = len(vectors[0])
        if self._dimension_from_config and self.dimension != dimension:
            raise ValueError(
                f"Mistral embedding dimension mismatch: expected {self.dimension}, got {dimension}"
            )

        self.dimension = dimension

        return EmbeddingResult(
            vectors=vectors,
            provider=self.provider,
            model=self.model,
            dimension=dimension,
            raw={"adapter": "MistralEmbeddingClient", "response": body},
        )
