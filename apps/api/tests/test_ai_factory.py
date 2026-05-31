import asyncio

import pytest

from app.services.ai.clients import LLMMessage, RerankCandidate, RerankResult
from app.services.ai.factory import (
    get_embedding_client,
    get_llm_client,
    get_ocr_client,
    get_reranker_client,
)
from app.services.ai.embedding_adapters import MistralEmbeddingClient
from app.services.ai.llm_adapters import MistralLLMClient
from app.services.ai.ocr_adapters import MistralOcrClient, NoopOcrClient
from app.services.ai.reranker_adapters import JinaRerankerClient


class DummyResponse:
    def __init__(self, json_data):
        self._json = json_data

    def raise_for_status(self):
        return None

    def json(self):
        return self._json


class DummyJinaAsyncClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, api_url, json, headers):
        assert api_url == "https://api.jina.ai/v1/rerank"
        assert json["model"] == "jina-reranker-v2-base-multilingual"
        assert json["query"] == "test query"
        assert json["documents"] == ["first", "second"]
        assert headers["Authorization"] == "Bearer test-key"
        return DummyResponse({
            "results": [
                {"index": 1, "relevance_score": 0.9},
                {"index": 0, "relevance_score": 0.3},
            ]
        })


class DummyMistralLLMAsyncClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, api_url, json, headers):
        assert api_url == "https://api.mistral.ai/v1/chat/completions"
        assert json["model"] == "mistral-medium-latest"
        assert json["messages"] == [{"role": "user", "content": "hello"}]
        assert json["temperature"] == 0.1
        assert json["max_tokens"] == 32
        assert headers["Authorization"] == "Bearer test-key"
        return DummyResponse({
            "choices": [
                {"message": {"role": "assistant", "content": "Bonjour"}}
            ]
        })


class TestAIClientFactory:
    def test_default_embedding_client_is_local(self):
        client = get_embedding_client()

        assert client.provider == "local"
        assert client.model == "hash-embedding-v1"
        assert client.dimension == 384

    def test_embedding_client_can_be_selected_from_env(self, monkeypatch):
        monkeypatch.setenv("EMBEDDING_PROVIDER", "mistral")

        client = get_embedding_client()

        assert isinstance(client, MistralEmbeddingClient)
        assert client.provider == "mistral"
        assert client.model == "mistral-embed"

    def test_embedding_client_provider_argument_overrides_env(self, monkeypatch):
        monkeypatch.setenv("EMBEDDING_PROVIDER", "local")

        client = get_embedding_client(provider="mistral")

        assert isinstance(client, MistralEmbeddingClient)
        assert client.provider == "mistral"

    def test_embedding_client_can_be_selected_from_preset(self, monkeypatch):
        monkeypatch.setenv("AI_BACKEND_PRESET", "poc-mistral-jina")

        client = get_embedding_client()

        assert isinstance(client, MistralEmbeddingClient)
        assert client.provider == "mistral"

    def test_embedding_preset_overrides_provider_env(self, monkeypatch):
        monkeypatch.setenv("AI_BACKEND_PRESET", "poc-mistral-jina")
        monkeypatch.setenv("EMBEDDING_PROVIDER", "local")

        client = get_embedding_client()

        assert isinstance(client, MistralEmbeddingClient)
        assert client.provider == "mistral"

    def test_embedding_provider_argument_overrides_preset(self, monkeypatch):
        monkeypatch.setenv("AI_BACKEND_PRESET", "local")

        client = get_embedding_client(provider="mistral")

        assert isinstance(client, MistralEmbeddingClient)
        assert client.provider == "mistral"

    def test_unknown_embedding_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown embedding provider"):
            get_embedding_client(provider="unknown")

    def test_reranker_client_can_be_selected_from_env(self, monkeypatch):
        monkeypatch.setenv("RERANKER_PROVIDER", "jina")
        monkeypatch.setenv("JINA_RERANKER_MODEL", "jina-reranker-v2-base-multilingual")

        client = get_reranker_client()

        assert isinstance(client, JinaRerankerClient)
        assert client.provider == "jina"
        assert client.model == "jina-reranker-v2-base-multilingual"

    def test_reranker_client_provider_argument_overrides_env(self, monkeypatch):
        monkeypatch.setenv("RERANKER_PROVIDER", "local")

        client = get_reranker_client(provider="jina")

        assert isinstance(client, JinaRerankerClient)
        assert client.provider == "jina"

    def test_reranker_client_can_be_selected_from_preset(self, monkeypatch):
        monkeypatch.setenv("AI_BACKEND_PRESET", "poc-mistral-jina")

        client = get_reranker_client()

        assert isinstance(client, JinaRerankerClient)
        assert client.provider == "jina"

    def test_default_llm_and_reranker_clients_are_local(self):
        llm_client = get_llm_client()
        reranker_client = get_reranker_client()

        assert llm_client.provider == "local"
        assert reranker_client.provider == "local"

    def test_default_ocr_client_is_noop(self):
        client = get_ocr_client()

        assert isinstance(client, NoopOcrClient)
        assert client.provider == "noop"
        assert client.enabled is False

    def test_ocr_client_can_be_selected_from_env(self, monkeypatch):
        monkeypatch.setenv("OCR_PROVIDER", "mistral")
        monkeypatch.setenv("MISTRAL_OCR_MODEL", "mistral-ocr-latest")

        client = get_ocr_client()

        assert isinstance(client, MistralOcrClient)
        assert client.provider == "mistral"
        assert client.model == "mistral-ocr-latest"

    def test_unknown_ocr_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown OCR provider"):
            get_ocr_client(provider="unknown")

    def test_llm_client_can_be_selected_from_env(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "mistral")
        monkeypatch.setenv("MISTRAL_LLM_MODEL", "mistral-medium-latest")

        client = get_llm_client()

        assert isinstance(client, MistralLLMClient)
        assert client.provider == "mistral"
        assert client.model == "mistral-medium-latest"

    def test_llm_client_provider_argument_overrides_env(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "local")

        client = get_llm_client(provider="mistral")

        assert isinstance(client, MistralLLMClient)
        assert client.provider == "mistral"

    def test_llm_client_can_be_selected_from_preset(self, monkeypatch):
        monkeypatch.setenv("AI_BACKEND_PRESET", "poc-mistral-jina")

        client = get_llm_client()

        assert isinstance(client, MistralLLMClient)
        assert client.provider == "mistral"

    def test_mistral_llm_client_generates(self, monkeypatch):
        monkeypatch.setenv("MISTRAL_EMBED_API_KEY", "test-key")
        monkeypatch.setenv("MISTRAL_LLM_MODEL", "mistral-medium-latest")
        monkeypatch.setattr("httpx.AsyncClient", DummyMistralLLMAsyncClient)

        client = MistralLLMClient()
        result = asyncio.run(
            client.generate(
                [LLMMessage(role="user", content="hello")],
                temperature=0.1,
                max_tokens=32,
            )
        )

        assert result.provider == "mistral"
        assert result.model == "mistral-medium-latest"
        assert result.text == "Bonjour"
        assert result.raw is not None
        assert result.raw["adapter"] == "MistralLLMClient"

    def test_jina_reranker_client_reranks(self, monkeypatch):
        monkeypatch.setenv("JINA_API_KEY", "test-key")
        monkeypatch.setenv("JINA_RERANKER_MODEL", "jina-reranker-v2-base-multilingual")
        monkeypatch.setattr("httpx.AsyncClient", DummyJinaAsyncClient)

        client = JinaRerankerClient()
        candidates = [
            RerankCandidate(id="a", text="first"),
            RerankCandidate(id="b", text="second"),
        ]

        result = asyncio.run(client.rerank("test query", candidates, top_k=1))

        assert result == [RerankResult(id="b", score=0.9, rank=1)]
