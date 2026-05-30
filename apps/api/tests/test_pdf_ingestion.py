import asyncio
from uuid import UUID

import pytest
from fastapi import HTTPException

from app.api.documentary import _chunk_document_metadata
from app.api import documentary
from app.services.documentary import ingestion
from app.services.documentary.chunking import chunk_text


class FakePdfPage:
    def __init__(self, text):
        self._text = text

    def extract_text(self):
        if isinstance(self._text, Exception):
            raise self._text
        return self._text


class FakePdfReader:
    def __init__(self, path):
        self.pages = []


def _reader_with_pages(pages):
    class Reader(FakePdfReader):
        def __init__(self, path):
            self.pages = [FakePdfPage(page) for page in pages]

    return Reader


def test_extract_pdf_returns_structured_success(monkeypatch):
    monkeypatch.setattr(
        ingestion,
        "PdfReader",
        _reader_with_pages(
            [
                "Titre court\nUn contenu exploitable sur la premiere page.",
                "Deuxieme page avec texte utile.",
            ]
        ),
    )

    result = ingestion.extract_pdf("/tmp/fake.pdf")
    metadata = result.metadata()

    assert result.status == "success"
    assert result.page_count == 2
    assert result.pages_with_text == 2
    assert result.empty_pages == []
    assert result.errors == []
    assert "[PAGE 1]" in result.raw_text
    assert "[SECTION Titre court]" in result.raw_text
    assert metadata["extraction"]["method"] == "pypdf.extract_text"
    assert metadata["extracted_pages"][0]["page"] == 1
    assert metadata["extracted_pages"][0]["section_title"] == "Titre court"


def test_extract_pdf_marks_empty_pdf_as_failed(monkeypatch):
    monkeypatch.setattr(ingestion, "PdfReader", _reader_with_pages(["", "   "]))

    result = ingestion.extract_pdf("/tmp/fake.pdf")

    assert result.status == "failed"
    assert result.pages_with_text == 0
    assert result.empty_pages == [1, 2]
    assert "possible_scan_or_empty_text" in result.warnings
    assert result.raw_text == ""


def test_extract_pdf_marks_partial_when_some_pages_are_empty(monkeypatch):
    monkeypatch.setattr(ingestion, "PdfReader", _reader_with_pages(["Texte utile.", ""]))

    result = ingestion.extract_pdf("/tmp/fake.pdf")

    assert result.status == "partial"
    assert result.pages_with_text == 1
    assert result.empty_pages == [2]
    assert "possible_scan_or_empty_text" in result.warnings


def test_extract_pdf_records_page_errors(monkeypatch):
    monkeypatch.setattr(
        ingestion,
        "PdfReader",
        _reader_with_pages(["Texte utile.", RuntimeError("broken page")]),
    )

    result = ingestion.extract_pdf("/tmp/fake.pdf")

    assert result.status == "partial"
    assert result.empty_pages == [2]
    assert result.errors
    assert "page_2: RuntimeError: broken page" in result.errors


def test_chunk_text_preserves_page_range_and_section_title():
    chunks = chunk_text(
        "[PAGE 3]\n[SECTION Introduction]\nTexte utile pour le chunk.",
        chunk_size_words=30,
        chunk_overlap_words=5,
    )

    assert len(chunks) == 1
    assert chunks[0].page_start == 3
    assert chunks[0].page_end == 3
    assert chunks[0].metadata["section_title"] == "Introduction"


def test_chunk_document_metadata_excludes_extraction_payloads():
    metadata = {
        "role_documentaire": "source_factuelle",
        "statut_metadonnees": "brouillon",
        "extraction": {"status": "success"},
        "extracted_pages": [{"page": 1, "text": "large text"}],
    }

    assert _chunk_document_metadata(metadata) == {
        "role_documentaire": "source_factuelle",
        "statut_metadonnees": "brouillon",
    }


def test_get_document_extraction_returns_stored_report_without_reprocessing(monkeypatch):
    document_id = UUID("00000000-0000-0000-0000-000000000001")

    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, query, params):
            assert params == (document_id,)

        def fetchone(self):
            return {
                "id": document_id,
                "title": "Document PDF",
                "metadata": {
                    "extraction": {
                        "method": "pypdf.extract_text",
                        "status": "success",
                        "page_count": 1,
                        "pages_with_text": 1,
                        "empty_pages": [],
                        "warnings": [],
                        "errors": [],
                    },
                    "extracted_pages": [
                        {
                            "page": 1,
                            "text": "Texte extrait",
                            "char_count": 13,
                            "section_title": None,
                        }
                    ],
                },
            }

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def cursor(self):
            return FakeCursor()

    monkeypatch.setattr(documentary, "get_connection", lambda: FakeConnection())

    response = asyncio.run(documentary.get_document_extraction(document_id))

    assert response.document_id == document_id
    assert response.extraction.status == "success"
    assert response.pages[0].page == 1
    assert response.pages[0].text == "Texte extrait"


def test_ingest_pdf_returns_409_on_duplicate_sha256(monkeypatch):
    class FakeUploadFile:
        filename = "duplicate.pdf"
        content_type = "application/pdf"

        async def read(self):
            return b"%PDF duplicate"

    class FakeExtraction:
        raw_text = "Texte extrait"
        status = "success"

        def metadata(self):
            return {
                "extraction": {
                    "method": "pypdf.extract_text",
                    "status": "success",
                    "page_count": 1,
                    "pages_with_text": 1,
                    "empty_pages": [],
                    "warnings": [],
                    "errors": [],
                },
                "extracted_pages": [
                    {
                        "page": 1,
                        "text": "Texte extrait",
                        "char_count": 13,
                        "section_title": None,
                    }
                ],
            }

    class FakeDiagnostic:
        constraint_name = "documents_sha256_key"

    class FakeUniqueViolation(Exception):
        diag = FakeDiagnostic()

    class FakeCursor:
        def __init__(self):
            self.executions = 0

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, query, params):
            self.executions += 1
            if self.executions == 2:
                raise FakeUniqueViolation("duplicate")

        def fetchone(self):
            return {"id": UUID("00000000-0000-0000-0000-000000000002")}

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def cursor(self):
            return FakeCursor()

    monkeypatch.setattr(documentary, "save_uploaded_file", lambda filename, content: ("/tmp/duplicate.pdf", "digest"))
    monkeypatch.setattr(documentary, "extract_pdf", lambda path: FakeExtraction())
    monkeypatch.setattr(documentary, "get_connection", lambda: FakeConnection())
    monkeypatch.setattr(documentary.psycopg.errors, "UniqueViolation", FakeUniqueViolation)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(documentary.ingest_pdf(FakeUploadFile(), source_code="duplicate"))

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == {
        "error": "document_already_exists",
        "sha256": "digest",
    }
