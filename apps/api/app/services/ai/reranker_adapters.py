from __future__ import annotations

import os

import httpx

from app.services.ai.clients import RerankCandidate, RerankResult


class LexicalOverlapReranker:
    provider = "local"
    model = "lexical-overlap-v1"

    async def rerank(
        self,
        query: str,
        candidates: list[RerankCandidate],
        *,
        top_k: int | None = None,
        metadata: dict | None = None,
    ) -> list[RerankResult]:
        query_terms = set(query.lower().split())
        scored: list[tuple[str, float]] = []

        for candidate in candidates:
            text_terms = set(candidate.text.lower().split())
            if not query_terms:
                score = 0.0
            else:
                score = len(query_terms & text_terms) / len(query_terms)
            scored.append((candidate.id, score))

        scored.sort(key=lambda item: item[1], reverse=True)

        if top_k is not None:
            scored = scored[:top_k]

        return [
            RerankResult(id=candidate_id, score=score, rank=i + 1)
            for i, (candidate_id, score) in enumerate(scored)
        ]


class JinaRerankerClient:
    provider = "jina"
    model: str

    def __init__(self, model: str | None = None) -> None:
        self.model = (
            model
            or os.getenv("JINA_RERANKER_MODEL")
            or "jina-reranker-v2-base-multilingual"
        ).strip()
        if not self.model:
            raise ValueError("JINA_RERANKER_MODEL must be configured for Jina reranking")

        self.api_url = os.getenv("JINA_RERANKER_API_URL", "https://api.jina.ai/v1/rerank").strip()
        if not self.api_url:
            raise ValueError("JINA_RERANKER_API_URL must be configured for Jina reranking")

    async def rerank(
        self,
        query: str,
        candidates: list[RerankCandidate],
        *,
        top_k: int | None = None,
        metadata: dict | None = None,
    ) -> list[RerankResult]:
        if not candidates:
            return []

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        api_key = os.getenv("JINA_API_KEY", "")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        payload: dict[str, object] = {
            "model": self.model,
            "query": query,
            "documents": [candidate.text for candidate in candidates],
            "return_documents": False,
        }
        if top_k is not None:
            payload["top_n"] = top_k

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(self.api_url, json=payload, headers=headers)
            response.raise_for_status()
            body = response.json()

        data = body.get("results", body.get("data"))
        if not isinstance(data, list):
            raise ValueError("Invalid response from Jina reranker provider")

        scored: list[tuple[int, float]] = []
        for item in data:
            if not isinstance(item, dict):
                raise ValueError("Invalid reranker response item")

            index = item.get("index")
            score = item.get("relevance_score", item.get("score"))
            if index is None or score is None:
                raise ValueError("Jina reranker response must include index and score")

            if not isinstance(index, int) or index < 0 or index >= len(candidates):
                raise ValueError("Jina reranker response index out of bounds")

            scored.append((index, float(score)))

        scored.sort(key=lambda item: item[1], reverse=True)
        if top_k is not None:
            scored = scored[:top_k]

        return [
            RerankResult(id=candidates[index].id, score=score, rank=i + 1)
            for i, (index, score) in enumerate(scored)
        ]
