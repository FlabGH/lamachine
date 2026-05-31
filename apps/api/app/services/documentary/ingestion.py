from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Literal

from pypdf import PdfReader

from app.services.ai.clients import OcrClient, OcrResult


STORAGE_DIR = Path("/tmp/lamachine_uploads")
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
PDF_HEADER = b"%PDF-"
PDF_EOF = b"%%EOF"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def save_uploaded_file(filename: str, content: bytes) -> tuple[str, str]:
    digest = sha256_bytes(content)
    safe_name = filename.replace("/", "_").replace("\\", "_")
    path = STORAGE_DIR / f"{digest}_{safe_name}"
    path.write_bytes(content)
    return str(path), digest


@dataclass(frozen=True)
class ExtractedPdfPage:
    page: int
    text: str
    char_count: int
    section_title: str | None = None


@dataclass(frozen=True)
class PdfExtraction:
    method: str
    status: Literal["success", "partial", "failed"]
    page_count: int
    pages_with_text: int
    empty_pages: list[int]
    warnings: list[str]
    errors: list[str]
    extracted_pages: list[ExtractedPdfPage]
    raw_text: str
    ocr_used: bool = False
    ocr_provider: str | None = None
    ocr_model: str | None = None
    ocr_trigger_reason: str | None = None
    ocr_pages_processed: int = 0

    def metadata(self) -> dict:
        return {
            "extraction": {
                "method": self.method,
                "status": self.status,
                "ocr_used": self.ocr_used,
                "ocr_provider": self.ocr_provider,
                "ocr_model": self.ocr_model,
                "ocr_trigger_reason": self.ocr_trigger_reason,
                "ocr_pages_processed": self.ocr_pages_processed,
                "page_count": self.page_count,
                "pages_with_text": self.pages_with_text,
                "empty_pages": self.empty_pages,
                "warnings": self.warnings,
                "errors": self.errors,
            },
            "extracted_pages": [asdict(page) for page in self.extracted_pages],
        }


SECTION_MAX_CHARS = 120


def _normalize_extracted_text(text: str) -> str:
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    normalized_lines: list[str] = []
    previous_empty = False

    for line in lines:
        if not line:
            if not previous_empty:
                normalized_lines.append("")
            previous_empty = True
            continue
        normalized_lines.append(line)
        previous_empty = False

    return "\n".join(normalized_lines).strip()


def _detect_section_title(text: str) -> str | None:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) < 2:
        return None

    candidate = lines[0]
    if len(candidate) > SECTION_MAX_CHARS:
        return None
    if candidate.endswith((".", ",", ";", ":")):
        return None
    if len(candidate.split()) > 14:
        return None

    return candidate


def _format_page_text(page: ExtractedPdfPage) -> str:
    parts = [f"[PAGE {page.page}]"]
    if page.section_title:
        parts.append(f"[SECTION {page.section_title}]")
    parts.append(page.text)
    return "\n".join(parts)


def _failed_pdf_extraction(error: Exception) -> PdfExtraction:
    return PdfExtraction(
        method="pypdf.extract_text",
        status="failed",
        page_count=0,
        pages_with_text=0,
        empty_pages=[],
        warnings=["possible_scan_or_empty_text"],
        errors=[f"document: {error.__class__.__name__}: {error}"],
        extracted_pages=[],
        raw_text="",
    )


def extract_pdf(path: str) -> PdfExtraction:
    try:
        reader = PdfReader(path)
    except Exception as exc:  # pragma: no cover - depends on malformed PDFs.
        return _failed_pdf_extraction(exc)

    extracted_pages: list[ExtractedPdfPage] = []
    empty_pages: list[int] = []
    warnings: list[str] = []
    errors: list[str] = []

    for i, page in enumerate(reader.pages, start=1):
        try:
            text = _normalize_extracted_text(page.extract_text() or "")
        except Exception as exc:  # pragma: no cover - depends on malformed PDFs.
            errors.append(f"page_{i}: {exc.__class__.__name__}: {exc}")
            empty_pages.append(i)
            continue

        if not text:
            empty_pages.append(i)
            continue

        extracted_pages.append(
            ExtractedPdfPage(
                page=i,
                text=text,
                char_count=len(text),
                section_title=_detect_section_title(text),
            )
        )

    page_count = len(reader.pages)
    pages_with_text = len(extracted_pages)
    raw_text = "\n\n".join(_format_page_text(page) for page in extracted_pages).strip()

    if pages_with_text == 0:
        status: Literal["success", "partial", "failed"] = "failed"
        warnings.append("possible_scan_or_empty_text")
    elif empty_pages or errors:
        status = "partial"
        warnings.append("possible_scan_or_empty_text")
    else:
        status = "success"

    if page_count and pages_with_text / page_count < 0.5 and "possible_scan_or_empty_text" not in warnings:
        warnings.append("possible_scan_or_empty_text")
        status = "partial"

    return PdfExtraction(
        method="pypdf.extract_text",
        status=status,
        page_count=page_count,
        pages_with_text=pages_with_text,
        empty_pages=empty_pages,
        warnings=warnings,
        errors=errors,
        extracted_pages=extracted_pages,
        raw_text=raw_text,
    )


def should_attempt_ocr(extraction: PdfExtraction) -> bool:
    return (
        extraction.status in {"failed", "partial"}
        and "possible_scan_or_empty_text" in extraction.warnings
    )


def clean_pdf_for_ocr(path: str) -> tuple[str, list[str], list[str]]:
    data = Path(path).read_bytes()
    if data.startswith(PDF_HEADER):
        return path, [], []

    pdf_start = data.find(PDF_HEADER)
    pdf_end = data.rfind(PDF_EOF)
    if pdf_start < 0 or pdf_end < pdf_start:
        return path, [], ["ocr_clean_pdf: missing_pdf_markers"]

    clean_content = data[pdf_start:pdf_end + len(PDF_EOF)]
    digest = sha256_bytes(clean_content)
    clean_path = STORAGE_DIR / f"{digest}_ocr_clean.pdf"
    clean_path.write_bytes(clean_content)

    return str(clean_path), ["ocr_cleaned_multipart_pdf_envelope"], []


def _extraction_from_ocr(
    ocr_result: OcrResult,
    *,
    trigger_reason: str,
    warnings: list[str] | None = None,
) -> PdfExtraction:
    extracted_pages: list[ExtractedPdfPage] = []
    for page in ocr_result.pages:
        text = _normalize_extracted_text(page.text)
        if not text:
            continue

        extracted_pages.append(
            ExtractedPdfPage(
                page=page.page,
                text=text,
                char_count=len(text),
                section_title=_detect_section_title(text),
            )
        )

    pages_with_text = len(extracted_pages)
    page_count = max((page.page for page in ocr_result.pages), default=pages_with_text)
    extracted_page_numbers = {page.page for page in extracted_pages}
    empty_pages = [
        page.page
        for page in ocr_result.pages
        if page.page not in extracted_page_numbers
    ]
    raw_text = "\n\n".join(_format_page_text(page) for page in extracted_pages).strip()
    status: Literal["success", "partial", "failed"]
    if pages_with_text == 0:
        status = "failed"
    elif empty_pages:
        status = "partial"
    else:
        status = "success"

    return PdfExtraction(
        method=f"pypdf.extract_text+{ocr_result.provider}.ocr",
        status=status,
        page_count=page_count,
        pages_with_text=pages_with_text,
        empty_pages=empty_pages,
        warnings=warnings or [],
        errors=[],
        extracted_pages=extracted_pages,
        raw_text=raw_text,
        ocr_used=True,
        ocr_provider=ocr_result.provider,
        ocr_model=ocr_result.model,
        ocr_trigger_reason=trigger_reason,
        ocr_pages_processed=ocr_result.pages_processed,
    )


async def extract_pdf_with_optional_ocr(
    path: str,
    *,
    ocr_client: OcrClient | None = None,
) -> PdfExtraction:
    extraction = extract_pdf(path)
    if not should_attempt_ocr(extraction):
        return extraction

    trigger_reason = "possible_scan_or_empty_text"
    if ocr_client is None or not getattr(ocr_client, "enabled", False):
        return replace(
            extraction,
            ocr_provider=getattr(ocr_client, "provider", None),
            ocr_model=getattr(ocr_client, "model", None),
            ocr_trigger_reason=trigger_reason,
        )

    ocr_path, clean_warnings, clean_errors = clean_pdf_for_ocr(path)
    if clean_errors:
        return replace(
            extraction,
            warnings=[*extraction.warnings, *clean_warnings],
            errors=[*extraction.errors, *clean_errors],
            ocr_provider=ocr_client.provider,
            ocr_model=ocr_client.model,
            ocr_trigger_reason=trigger_reason,
        )

    try:
        ocr_result = await ocr_client.extract_pdf(
            ocr_path,
            metadata={"trigger_reason": trigger_reason, "original_path": path},
        )
    except Exception as exc:
        return replace(
            extraction,
            warnings=[*extraction.warnings, *clean_warnings],
            errors=[
                *extraction.errors,
                f"ocr: {exc.__class__.__name__}: {exc}",
            ],
            ocr_provider=ocr_client.provider,
            ocr_model=ocr_client.model,
            ocr_trigger_reason=trigger_reason,
        )

    return _extraction_from_ocr(
        ocr_result,
        trigger_reason=trigger_reason,
        warnings=clean_warnings,
    )


def extract_pdf_text(path: str) -> str:
    return extract_pdf(path).raw_text


def normalize_text(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.splitlines()).strip()
