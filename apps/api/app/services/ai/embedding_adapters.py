from __future__ import annotations

import hashlib
import math
from typing import Any

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
