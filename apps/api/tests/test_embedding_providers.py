import asyncio
import pytest

from app.services.ai.embedding_adapters import MistralEmbeddingClient


class TestMistralEmbeddingClient:
    def test_default_dimension_is_1024(self, mock_mistral_api):
        mock_mistral_api.delenv("MISTRAL_EMBED_DIMENSION", raising=False)

        client = MistralEmbeddingClient()

        assert client.dimension == 1024

        result = asyncio.run(client.embed_texts(["hello world"]))

        assert result.provider == "mistral"
        assert result.model == "mistral-embed"
        assert result.dimension == 1024
        assert len(result.vectors) == 1
        assert len(result.vectors[0]) == 1024
        assert result.raw["adapter"] == "MistralEmbeddingClient"

    def test_custom_dimension_is_respected(self, mock_mistral_api):
        mock_mistral_api.setenv("MISTRAL_EMBED_DIMENSION", "1024")

        client = MistralEmbeddingClient()

        assert client.dimension == 1024

        result = asyncio.run(client.embed_texts(["hello world"]))

        assert result.dimension == 1024

    def test_embed_texts_raises_when_api_url_missing(self, monkeypatch):
        monkeypatch.delenv("MISTRAL_EMBED_API_URL", raising=False)
        monkeypatch.setenv("MISTRAL_EMBED_DIMENSION", "1024")
        monkeypatch.setattr("httpx.AsyncClient", type("MockClient", (), {
            "__init__": lambda self, *args, **kwargs: None,
            "__aenter__": lambda self: self,
            "__aexit__": lambda self, exc_type, exc, tb: False,
            "post": lambda self, api_url, json, headers: type("R", (), {"raise_for_status": lambda self: None, "json": lambda self: {"data": [{"embedding": [0.0] * 1024}]}})(),
        }))

        client = MistralEmbeddingClient()

        with pytest.raises(ValueError, match="MISTRAL_EMBED_API_URL must be configured"):
            asyncio.run(client.embed_texts(["hello world"]))
