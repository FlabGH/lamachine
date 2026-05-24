import pytest

from app.services.ai.factory import get_embedding_client, get_llm_client, get_reranker_client
from app.services.ai.embedding_adapters import MistralEmbeddingClient


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

    def test_unknown_embedding_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown embedding provider"):
            get_embedding_client(provider="unknown")

    def test_default_llm_and_reranker_clients_are_local(self):
        llm_client = get_llm_client()
        reranker_client = get_reranker_client()

        assert llm_client.provider == "local"
        assert reranker_client.provider == "local"
