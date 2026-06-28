from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from app.services.ai.clients import OcrClient
from app.services.documentary.ingestion import (
    ExtractedPdfPage,
    extract_pdf_with_optional_ocr,
    normalize_text,
)


@dataclass(frozen=True)
class LoaderInfo:
    name: str
    version: str
    description: str
    mime_types: list[str]
    file_extensions: list[str]
    ocr_supported: bool = False


@dataclass(frozen=True)
class LoaderInput:
    mime_type: str
    filename: str | None = None
    path: str | None = None
    text: str | None = None
    content: bytes | None = None
    ocr_client: OcrClient | None = None


@dataclass(frozen=True)
class LoadedPage:
    page: int | None
    text: str
    char_count: int
    section_title: str | None = None
    extraction_source: str | None = None
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class LoaderTrace:
    name: str
    version: str
    mime_type: str
    file_extension: str | None
    status: str
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    ocr_used: bool = False
    ocr_provider: str | None = None
    ocr_model: str | None = None

    def metadata(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "mime_type": self.mime_type,
            "file_extension": self.file_extension,
            "status": self.status,
            "warnings": self.warnings,
            "errors": self.errors,
            "ocr_used": self.ocr_used,
            "ocr_provider": self.ocr_provider,
            "ocr_model": self.ocr_model,
        }


@dataclass(frozen=True)
class LoaderResult:
    raw_text: str
    status: str
    pages: list[LoadedPage]
    trace: LoaderTrace
    extraction_metadata: dict = field(default_factory=dict)

    def metadata(self) -> dict:
        return {
            "loader": self.trace.metadata(),
            **self.extraction_metadata,
        }


class DocumentLoader(Protocol):
    info: LoaderInfo

    async def load(self, input: LoaderInput) -> LoaderResult:
        ...


def _file_extension(filename: str | None, path: str | None = None) -> str | None:
    candidate = filename or path
    if not candidate:
        return None
    suffix = Path(candidate).suffix.lower().lstrip(".")
    return suffix or None


def _loaded_pdf_page(page: ExtractedPdfPage) -> LoadedPage:
    return LoadedPage(
        page=page.page,
        text=page.text,
        char_count=page.char_count,
        section_title=page.section_title,
        extraction_source=page.extraction_source,
        metadata=page.metadata(),
    )


class PdfDocumentLoader:
    info = LoaderInfo(
        name="pdf_pypdf_ocr_v1",
        version="1",
        description="PDF loader using pypdf text extraction with optional OCR fallback.",
        mime_types=["application/pdf"],
        file_extensions=["pdf"],
        ocr_supported=True,
    )

    async def load(self, input: LoaderInput) -> LoaderResult:
        if not input.path:
            raise ValueError("PDF loader requires a stored file path")

        extraction = await extract_pdf_with_optional_ocr(
            input.path,
            ocr_client=input.ocr_client,
        )
        trace = LoaderTrace(
            name=self.info.name,
            version=self.info.version,
            mime_type=input.mime_type or "application/pdf",
            file_extension=_file_extension(input.filename, input.path),
            status=extraction.status,
            warnings=extraction.warnings,
            errors=extraction.errors,
            ocr_used=extraction.ocr_used,
            ocr_provider=extraction.ocr_provider,
            ocr_model=extraction.ocr_model,
        )
        return LoaderResult(
            raw_text=extraction.raw_text,
            status=extraction.status,
            pages=[_loaded_pdf_page(page) for page in extraction.extracted_pages],
            trace=trace,
            extraction_metadata=extraction.metadata(),
        )


class PlainTextDocumentLoader:
    info = LoaderInfo(
        name="plain_text_v1",
        version="1",
        description="Plain text loader preserving line breaks after whitespace normalization.",
        mime_types=["text/plain"],
        file_extensions=["txt"],
        ocr_supported=False,
    )

    async def load(self, input: LoaderInput) -> LoaderResult:
        text = input.text
        if text is None and input.content is not None:
            text = input.content.decode("utf-8", errors="replace")
        raw_text = normalize_text(text or "")
        trace = LoaderTrace(
            name=self.info.name,
            version=self.info.version,
            mime_type=input.mime_type or "text/plain",
            file_extension=_file_extension(input.filename, input.path),
            status="success",
        )
        return LoaderResult(
            raw_text=raw_text,
            status="success",
            pages=[
                LoadedPage(
                    page=None,
                    text=raw_text,
                    char_count=len(raw_text),
                    extraction_source="text",
                )
            ],
            trace=trace,
            extraction_metadata={
                "extraction": {
                    "method": "plain_text.normalize_text",
                    "status": "success",
                    "ocr_used": False,
                    "warnings": [],
                    "errors": [],
                }
            },
        )


LOADERS: dict[str, DocumentLoader] = {
    PdfDocumentLoader.info.name: PdfDocumentLoader(),
    PlainTextDocumentLoader.info.name: PlainTextDocumentLoader(),
}


def get_loader(name: str) -> DocumentLoader:
    normalized_name = name.strip()
    try:
        return LOADERS[normalized_name]
    except KeyError as exc:
        raise ValueError(f"Unsupported document loader: {name}") from exc


def list_loaders() -> list[LoaderInfo]:
    return [loader.info for loader in LOADERS.values()]
