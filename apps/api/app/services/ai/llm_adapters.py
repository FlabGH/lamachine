from __future__ import annotations

import os
from typing import Any

import httpx

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


class MistralLLMClient:
    provider = "mistral"

    def __init__(self, model: str | None = None) -> None:
        self.model = (
            model
            or os.getenv("MISTRAL_LLM_MODEL")
            or "mistral-medium-latest"
        ).strip()
        if not self.model:
            raise ValueError("MISTRAL_LLM_MODEL must be configured for Mistral LLM")

        self.api_url = os.getenv(
            "MISTRAL_LLM_API_URL",
            "https://api.mistral.ai/v1/chat/completions",
        ).strip()
        if not self.api_url:
            raise ValueError("MISTRAL_LLM_API_URL must be configured for Mistral LLM")

    async def generate(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> LLMResult:
        api_key = os.getenv("MISTRAL_LLM_API_KEY") or os.getenv("MISTRAL_EMBED_API_KEY", "")
        if not api_key:
            raise ValueError("MISTRAL_LLM_API_KEY or MISTRAL_EMBED_API_KEY must be configured")

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": message.role, "content": message.content}
                for message in messages
            ],
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(self.api_url, json=payload, headers=headers)
            response.raise_for_status()
            body = response.json()

        choices = body.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Invalid response from Mistral LLM provider")

        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise ValueError("Invalid Mistral LLM response choice")

        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise ValueError("Mistral LLM response is missing message")

        content = message.get("content")
        if isinstance(content, str):
            text = content
        elif isinstance(content, list):
            text = "".join(
                item.get("text", "")
                for item in content
                if isinstance(item, dict) and item.get("type") == "text"
            )
        else:
            raise ValueError("Mistral LLM response message content is invalid")

        return LLMResult(
            text=text,
            provider=self.provider,
            model=self.model,
            raw={"adapter": "MistralLLMClient", "response": body},
        )
