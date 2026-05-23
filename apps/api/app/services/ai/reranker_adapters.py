from __future__ import annotations

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
