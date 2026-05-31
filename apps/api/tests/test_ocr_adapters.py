import asyncio

from app.services.ai.ocr_adapters import MistralOcrClient, NoopOcrClient


class DummyResponse:
    def __init__(self, json_data):
        self._json = json_data

    def raise_for_status(self):
        return None

    def json(self):
        return self._json


class DummyMistralOcrAsyncClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, api_url, json, headers):
        assert api_url == "https://api.mistral.ai/v1/ocr"
        assert json["model"] == "mistral-ocr-latest"
        assert json["document"]["type"] == "document_url"
        assert json["document"]["document_url"].startswith(
            "data:application/pdf;base64,"
        )
        assert headers["Authorization"] == "Bearer test-key"
        return DummyResponse(
            {
                "model": "mistral-ocr-latest",
                "pages": [
                    {"index": 0, "markdown": "# Page 1\nTexte reconnu"},
                    {"index": 1, "markdown": "Page 2"},
                ],
                "usage_info": {"pages_processed": 2},
            }
        )


def test_noop_ocr_client_returns_empty_result():
    client = NoopOcrClient()

    result = asyncio.run(client.extract_pdf("/tmp/missing.pdf"))

    assert result.provider == "noop"
    assert result.model == "ocr-disabled"
    assert result.pages == []
    assert result.pages_processed == 0


def test_mistral_ocr_client_parses_pages(monkeypatch, tmp_path):
    pdf_path = tmp_path / "scan.pdf"
    pdf_path.write_bytes(b"%PDF-1.7\nscan\n%%EOF")
    monkeypatch.setenv("MISTRAL_OCR_API_KEY", "test-key")
    monkeypatch.setenv("MISTRAL_OCR_MODEL", "mistral-ocr-latest")
    monkeypatch.setattr("httpx.AsyncClient", DummyMistralOcrAsyncClient)

    client = MistralOcrClient()
    result = asyncio.run(client.extract_pdf(str(pdf_path)))

    assert result.provider == "mistral"
    assert result.model == "mistral-ocr-latest"
    assert result.pages_processed == 2
    assert [page.page for page in result.pages] == [1, 2]
    assert result.pages[0].text == "# Page 1\nTexte reconnu"
