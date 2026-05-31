import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))


class DummyResponse:
    def __init__(self, json_data):
        self._json = json_data

    def raise_for_status(self):
        return None

    def json(self):
        return self._json


class DummyAsyncClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, api_url, json, headers):
        return DummyResponse({"data": [{"embedding": [0.0] * 1024}]})


@pytest.fixture(autouse=True)
def clear_provider_env(monkeypatch):
    monkeypatch.delenv("AI_BACKEND_PRESET", raising=False)
    monkeypatch.delenv("EMBEDDING_PROVIDER", raising=False)
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("OCR_PROVIDER", raising=False)
    monkeypatch.delenv("RERANKER_PROVIDER", raising=False)
    yield


@pytest.fixture
def mock_mistral_api(monkeypatch):
    monkeypatch.setenv("MISTRAL_EMBED_API_URL", "https://api.mistral.ai/v1/embeddings")
    monkeypatch.setenv("MISTRAL_EMBED_API_KEY", "test-key")
    monkeypatch.setattr("httpx.AsyncClient", DummyAsyncClient)
    return monkeypatch
