from __future__ import annotations

import asyncio

import pytest

from app.services.documentary import loaders
from app.services.documentary.ingestion import ExtractedPdfPage, PdfExtraction
from app.services.documentary.loaders import (
    LoaderInput,
    get_loader,
    list_loaders,
)


def test_loader_registry_exposes_pdf_and_plain_text_loaders():
    names = {loader.name for loader in list_loaders()}

    assert names == {"pdf_pypdf_ocr_v1", "plain_text_v1"}
    assert get_loader("pdf_pypdf_ocr_v1").info.ocr_supported is True
    assert get_loader("plain_text_v1").info.ocr_supported is False

    with pytest.raises(ValueError, match="Unsupported document loader"):
        get_loader("legacy_loader")


def test_plain_text_loader_normalizes_text_and_traces_loader():
    loader = get_loader("plain_text_v1")

    result = asyncio.run(
        loader.load(
            LoaderInput(
                mime_type="text/plain",
                filename="document.txt",
                text="Ligne 1  \n\nLigne 2  ",
            )
        )
    )

    assert result.raw_text == "Ligne 1\n\nLigne 2"
    assert result.status == "success"
    assert result.pages[0].page is None
    assert result.pages[0].extraction_source == "text"
    assert result.trace.name == "plain_text_v1"
    assert result.trace.ocr_used is False
    assert result.metadata()["loader"]["name"] == "plain_text_v1"
    assert result.metadata()["extraction"]["method"] == "plain_text.normalize_text"


def test_pdf_loader_wraps_existing_pdf_extraction(monkeypatch):
    async def fake_extract_pdf_with_optional_ocr(path, *, ocr_client=None):
        assert path == "/tmp/document.pdf"
        assert ocr_client == "ocr"
        return PdfExtraction(
            method="pypdf.extract_text",
            status="partial",
            page_count=2,
            pages_with_text=1,
            empty_pages=[2],
            warnings=["possible_scan_or_empty_text"],
            errors=["page_2: unreadable"],
            extracted_pages=[
                ExtractedPdfPage(
                    page=1,
                    text="Texte page",
                    char_count=10,
                    section_title="Intro",
                )
            ],
            raw_text="[PAGE 1]\n[SECTION Intro]\nTexte page",
            ocr_used=True,
            ocr_provider="test-ocr",
            ocr_model="ocr-v1",
            ocr_pages_processed=1,
        )

    monkeypatch.setattr(
        loaders,
        "extract_pdf_with_optional_ocr",
        fake_extract_pdf_with_optional_ocr,
    )

    result = asyncio.run(
        get_loader("pdf_pypdf_ocr_v1").load(
            LoaderInput(
                mime_type="application/pdf",
                filename="document.pdf",
                path="/tmp/document.pdf",
                ocr_client="ocr",
            )
        )
    )

    assert result.raw_text.startswith("[PAGE 1]")
    assert result.status == "partial"
    assert result.pages[0].page == 1
    assert result.pages[0].section_title == "Intro"
    assert result.trace.name == "pdf_pypdf_ocr_v1"
    assert result.trace.ocr_used is True
    assert result.trace.ocr_provider == "test-ocr"
    assert result.metadata()["loader"]["version"] == "1"
    assert result.metadata()["extraction"]["method"] == "pypdf.extract_text"


def test_pdf_loader_requires_path():
    with pytest.raises(ValueError, match="stored file path"):
        asyncio.run(
            get_loader("pdf_pypdf_ocr_v1").load(
                LoaderInput(mime_type="application/pdf", filename="document.pdf")
            )
        )
