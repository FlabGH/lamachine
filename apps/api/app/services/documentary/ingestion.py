from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from pypdf import PdfReader


STORAGE_DIR = Path("/tmp/lamachine_uploads")
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


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

    def metadata(self) -> dict:
        return {
            "extraction": {
                "method": self.method,
                "status": self.status,
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


def extract_pdf(path: str) -> PdfExtraction:
    reader = PdfReader(path)
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


def extract_pdf_text(path: str) -> str:
    return extract_pdf(path).raw_text


def normalize_text(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.splitlines()).strip()
