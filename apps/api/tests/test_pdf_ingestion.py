import asyncio
from uuid import UUID

import pytest
from fastapi import HTTPException

from app.services.ai.clients import OcrPage, OcrResult
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


def test_extract_pdf_with_optional_ocr_skips_ocr_on_success(monkeypatch):
    class FakeOcrClient:
        provider = "fake"
        model = "fake-ocr"
        enabled = True

        async def extract_pdf(self, path, *, metadata=None):
            raise AssertionError("OCR should not be called")

    monkeypatch.setattr(
        ingestion,
        "PdfReader",
        _reader_with_pages(
            [
                (
                    "Cette page contient un paragraphe complet et lisible. "
                    "Les phrases sont correctement ponctuees. "
                    "Le texte est assez dense pour ne pas ressembler a une page "
                    "fragmentaire issue d'une extraction PDF de mauvaise qualite. "
                )
                * 3
            ]
        ),
    )

    result = asyncio.run(
        ingestion.extract_pdf_with_optional_ocr(
            "/tmp/fake.pdf",
            ocr_client=FakeOcrClient(),
        )
    )

    assert result.status == "success"
    assert result.ocr_used is False
    assert result.ocr_trigger_reason is None
    assert result.layout_quality_status == "ok"


def test_extract_pdf_with_optional_ocr_keeps_pypdf_result_when_ocr_disabled(monkeypatch):
    class NoopOcrClient:
        provider = "noop"
        model = "ocr-disabled"
        enabled = False

    monkeypatch.setattr(ingestion, "PdfReader", _reader_with_pages([""]))

    result = asyncio.run(
        ingestion.extract_pdf_with_optional_ocr(
            "/tmp/fake.pdf",
            ocr_client=NoopOcrClient(),
        )
    )

    assert result.status == "failed"
    assert result.ocr_used is False
    assert result.ocr_provider == "noop"
    assert result.ocr_trigger_reason == "possible_scan_or_empty_text"


def test_extract_pdf_with_optional_ocr_uses_ocr_for_weak_pdf(monkeypatch, tmp_path):
    class FakeOcrClient:
        provider = "fake"
        model = "fake-ocr"
        enabled = True

        async def extract_pdf(self, path, *, metadata=None):
            assert metadata == {
                "trigger_reason": "possible_scan_or_empty_text",
                "original_path": str(pdf_path),
            }
            return OcrResult(
                pages=[OcrPage(page=1, text="Titre OCR\nTexte reconnu.")],
                provider=self.provider,
                model=self.model,
                pages_processed=1,
            )

    pdf_path = tmp_path / "scan.pdf"
    pdf_path.write_bytes(b"%PDF-1.7\nscan\n%%EOF")
    monkeypatch.setattr(ingestion, "PdfReader", _reader_with_pages([""]))

    result = asyncio.run(
        ingestion.extract_pdf_with_optional_ocr(
            str(pdf_path),
            ocr_client=FakeOcrClient(),
        )
    )
    metadata = result.metadata()["extraction"]

    assert result.status == "success"
    assert result.method == "pypdf.extract_text+fake.ocr"
    assert result.ocr_used is True
    assert result.ocr_provider == "fake"
    assert result.ocr_model == "fake-ocr"
    assert result.ocr_pages_processed == 1
    assert "[SECTION Titre OCR]" in result.raw_text
    assert metadata["ocr_used"] is True
    assert metadata["ocr_trigger_reason"] == "possible_scan_or_empty_text"
    assert result.extracted_pages[0].extraction_source == "ocr"


def test_extract_pdf_marks_weak_layout_pages_as_suspect(monkeypatch):
    monkeypatch.setattr(
        ingestion,
        "PdfReader",
        _reader_with_pages(
            [
                "38\nmilliardaires. L'innovation se retrouve souvent orientee vers",
                (
                    "Cette page contient un paragraphe complet. "
                    "Il est suffisamment long et ponctue pour etre considere correct. "
                )
                * 4,
            ]
        ),
    )

    result = ingestion.extract_pdf("/tmp/fake.pdf")
    metadata = result.metadata()["extraction"]

    assert result.status == "success"
    assert result.layout_quality_status == "suspect"
    assert result.layout_suspect_pages == [1]
    assert "short_text_page" in result.layout_warnings
    assert metadata["layout_quality_rules_version"] == "weak-layout-v1"
    assert metadata["layout_suspect_pages"] == [1]
    assert result.extracted_pages[0].layout_quality.status == "suspect"


def test_extract_pdf_with_optional_ocr_replaces_only_suspect_layout_pages(
    monkeypatch,
    tmp_path,
):
    class FakeOcrClient:
        provider = "fake"
        model = "fake-layout-ocr"
        enabled = True

        async def extract_pdf(self, path, *, metadata=None):
            assert metadata["trigger_reason"] == "weak_layout_quality"
            assert metadata["ocr_pages"] == [1]
            assert metadata["page_map"] == {1: 1}
            assert path == str(subset_path)
            return OcrResult(
                pages=[
                    OcrPage(
                        page=1,
                        text=(
                            "Mettre l'intelligence artificielle au service du bien commun\n"
                            "L'intelligence artificielle ouvre des possibilites immenses. "
                            "Nous proposons une maitrise democratique, des audits reguliers "
                            "et une mise au service de l'interet general."
                        ),
                    )
                ],
                provider=self.provider,
                model=self.model,
                pages_processed=1,
            )

    pdf_path = tmp_path / "weak-layout.pdf"
    pdf_path.write_bytes(b"%PDF-1.7\nbody\n%%EOF")
    subset_path = tmp_path / "subset.pdf"
    subset_path.write_bytes(b"%PDF-1.7\nsubset\n%%EOF")
    monkeypatch.setattr(
        ingestion,
        "PdfReader",
        _reader_with_pages(
            [
                "38\nmilliardaires. L'innovation se retrouve souvent orientee vers",
                (
                    "Cette page contient un paragraphe complet. "
                    "Il est suffisamment long et ponctue pour etre considere correct. "
                )
                * 4,
            ]
        ),
    )
    monkeypatch.setattr(
        ingestion,
        "build_pages_pdf_for_ocr",
        lambda path, pages: (str(subset_path), {1: 1}),
    )

    result = asyncio.run(
        ingestion.extract_pdf_with_optional_ocr(
            str(pdf_path),
            ocr_client=FakeOcrClient(),
        )
    )
    metadata = result.metadata()

    assert result.method == "pypdf.extract_text+fake.layout_ocr"
    assert result.ocr_used is True
    assert result.ocr_trigger_reason == "weak_layout_quality"
    assert result.layout_ocr_pages_requested == [1]
    assert result.layout_ocr_pages_replaced == [1]
    assert result.layout_ocr_pages_kept_original == []
    assert result.extracted_pages[0].extraction_source == "ocr"
    assert result.extracted_pages[1].extraction_source == "pypdf"
    assert "Mettre l'intelligence artificielle" in result.raw_text
    assert metadata["extracted_pages"][0]["layout_quality"]["original_char_count"] == 64
    assert metadata["extracted_pages"][0]["layout_quality"]["ocr_word_count"] > 0


def test_extract_pdf_with_optional_ocr_keeps_original_when_layout_ocr_is_noisy(
    monkeypatch,
    tmp_path,
):
    class FakeOcrClient:
        provider = "fake"
        model = "fake-layout-ocr"
        enabled = True

        async def extract_pdf(self, path, *, metadata=None):
            return OcrResult(
                pages=[OcrPage(page=1, text="### @@@ ### @@@")],
                provider=self.provider,
                model=self.model,
                pages_processed=1,
            )

    pdf_path = tmp_path / "weak-layout.pdf"
    pdf_path.write_bytes(b"%PDF-1.7\nbody\n%%EOF")
    subset_path = tmp_path / "subset.pdf"
    subset_path.write_bytes(b"%PDF-1.7\nsubset\n%%EOF")
    monkeypatch.setattr(
        ingestion,
        "PdfReader",
        _reader_with_pages(
            ["38\nmilliardaires. L'innovation se retrouve souvent orientee vers"]
        ),
    )
    monkeypatch.setattr(
        ingestion,
        "build_pages_pdf_for_ocr",
        lambda path, pages: (str(subset_path), {1: 1}),
    )

    result = asyncio.run(
        ingestion.extract_pdf_with_optional_ocr(
            str(pdf_path),
            ocr_client=FakeOcrClient(),
        )
    )

    assert result.ocr_used is False
    assert result.layout_ocr_pages_requested == [1]
    assert result.layout_ocr_pages_replaced == []
    assert result.layout_ocr_pages_kept_original == [1]
    assert result.extracted_pages[0].extraction_source == "pypdf"
    assert result.extracted_pages[0].layout_quality.status == (
        "ocr_attempted_no_improvement"
    )


def test_clean_pdf_for_ocr_repairs_multipart_envelope(tmp_path):
    wrapped_pdf = (
        b"--boundary\r\n"
        b"Content-Disposition: form-data; name=\"file\"; filename=\"scan.pdf\"\r\n"
        b"Content-Type: application/octet-stream\r\n\r\n"
        b"%PDF-1.7\nbody\n%%EOF\r\n--boundary--"
    )
    wrapped_path = tmp_path / "wrapped.pdf"
    wrapped_path.write_bytes(wrapped_pdf)

    clean_path, warnings, errors = ingestion.clean_pdf_for_ocr(str(wrapped_path))

    assert warnings == ["ocr_cleaned_multipart_pdf_envelope"]
    assert errors == []
    assert clean_path != str(wrapped_path)
    assert (tmp_path / "wrapped.pdf").read_bytes().startswith(b"--boundary")
    assert open(clean_path, "rb").read() == b"%PDF-1.7\nbody\n%%EOF"


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

    async def fake_extract_pdf_with_optional_ocr(path, *, ocr_client=None):
        return FakeExtraction()

    monkeypatch.setattr(documentary, "save_uploaded_file", lambda filename, content: ("/tmp/duplicate.pdf", "digest"))
    monkeypatch.setattr(documentary, "extract_pdf_with_optional_ocr", fake_extract_pdf_with_optional_ocr)
    monkeypatch.setattr(documentary, "get_ocr_client", lambda: None)
    monkeypatch.setattr(documentary, "get_connection", lambda: FakeConnection())
    monkeypatch.setattr(documentary.psycopg.errors, "UniqueViolation", FakeUniqueViolation)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(documentary.ingest_pdf(FakeUploadFile(), source_code="duplicate"))

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == {
        "error": "document_already_exists",
        "sha256": "digest",
    }
