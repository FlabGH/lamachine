from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Any

import httpx

from app.services.ai.clients import OcrPage, OcrResult


class NoopOcrClient:
    provider = "noop"
    model = "ocr-disabled"
    enabled = False

    async def extract_pdf(
        self,
        path: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> OcrResult:
        return OcrResult(
            pages=[],
            provider=self.provider,
            model=self.model,
            pages_processed=0,
            raw={"adapter": "NoopOcrClient"},
        )


class MistralOcrClient:
    provider = "mistral"
    enabled = True

    def __init__(self, model: str | None = None) -> None:
        self.model = (
            model
            or os.getenv("MISTRAL_OCR_MODEL")
            or "mistral-ocr-latest"
        ).strip()
        if not self.model:
            raise ValueError("MISTRAL_OCR_MODEL must be configured for Mistral OCR")

        self.api_url = os.getenv(
            "MISTRAL_OCR_API_URL",
            "https://api.mistral.ai/v1/ocr",
        ).strip()
        if not self.api_url:
            raise ValueError("MISTRAL_OCR_API_URL must be configured for Mistral OCR")

    async def extract_pdf(
        self,
        path: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> OcrResult:
        api_key = (
            os.getenv("MISTRAL_OCR_API_KEY")
            or os.getenv("MISTRAL_LLM_API_KEY")
            or os.getenv("MISTRAL_EMBED_API_KEY", "")
        )
        if not api_key:
            raise ValueError(
                "MISTRAL_OCR_API_KEY, MISTRAL_LLM_API_KEY or MISTRAL_EMBED_API_KEY "
                "must be configured"
            )

        pdf_base64 = base64.b64encode(Path(path).read_bytes()).decode("ascii")
        payload = {
            "model": self.model,
            "document": {
                "type": "document_url",
                "document_url": f"data:application/pdf;base64,{pdf_base64}",
            },
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(self.api_url, json=payload, headers=headers)
            response.raise_for_status()
            body = response.json()

        pages_body = body.get("pages")
        if not isinstance(pages_body, list):
            raise ValueError("Invalid response from Mistral OCR provider")

        pages: list[OcrPage] = []
        for fallback_index, item in enumerate(pages_body, start=1):
            if not isinstance(item, dict):
                raise ValueError("Invalid Mistral OCR page item")

            index = item.get("index")
            if isinstance(index, int):
                page_number = index + 1
            else:
                page_number = fallback_index

            text = item.get("markdown", item.get("text", ""))
            if not isinstance(text, str):
                raise ValueError("Invalid Mistral OCR page text")

            pages.append(OcrPage(page=page_number, text=text))

        usage_info = body.get("usage_info") or {}
        pages_processed = usage_info.get("pages_processed", len(pages))
        if not isinstance(pages_processed, int):
            pages_processed = len(pages)

        response_model = body.get("model")
        if not isinstance(response_model, str) or not response_model:
            response_model = self.model

        return OcrResult(
            pages=pages,
            provider=self.provider,
            model=response_model,
            pages_processed=pages_processed,
            raw={"adapter": "MistralOcrClient", "response": body},
        )
