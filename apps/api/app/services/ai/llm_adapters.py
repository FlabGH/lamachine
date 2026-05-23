from __future__ import annotations

from typing import Any

from app.services.ai.clients import LLMMessage, LLMResult


class ExtractiveNoteLLMClient:
    provider = "local"
    model = "extractive-note-v1"

    async def generate(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> LLMResult:
        user_content = "\n\n".join(m.content for m in messages if m.role == "user")

        text = (
            "# Note de riposte sourcée\n\n"
            "## Synthèse\n\n"
            "Cette note est générée à partir des passages retrouvés dans la base documentaire.\n\n"
            "## Éléments mobilisables\n\n"
            f"{user_content}\n\n"
            "## Limites\n\n"
            "Sortie extractive de test : aucun raisonnement politique autonome, aucun fait externe ajouté."
        )

        return LLMResult(
            text=text,
            provider=self.provider,
            model=self.model,
            raw={"adapter": "ExtractiveNoteLLMClient"},
        )
