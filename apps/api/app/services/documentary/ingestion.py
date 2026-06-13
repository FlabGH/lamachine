from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Literal

from pypdf import PdfReader, PdfWriter

from app.services.ai.clients import OcrClient, OcrResult


STORAGE_DIR = Path("/tmp/lamachine_uploads")
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
PDF_HEADER = b"%PDF-"
PDF_EOF = b"%%EOF"
LAYOUT_QUALITY_RULES_VERSION = "weak-layout-v1"
WEAK_LAYOUT_MIN_CHARS = 250
WEAK_LAYOUT_MIN_WORDS = 180
WEAK_LAYOUT_FRAGMENTED_MIN_LINES = 8
WEAK_LAYOUT_SHORT_LINE_CHARS = 35
WEAK_LAYOUT_SHORT_LINE_RATIO = 0.55
WEAK_LAYOUT_NUMERIC_TITLE_SHORT_LINE_RATIO = 0.45
WEAK_LAYOUT_MAX_PUNCTUATED_LINE_RATIO = 0.25
WEAK_LAYOUT_MIN_AVG_LINE_LENGTH = 45
OCR_MIN_WORD_GAIN_RATIO = 1.10
OCR_MIN_CHAR_GAIN_RATIO = 1.25
OCR_NOISE_MAX_SHORT_LINE_RATIO = 0.75
OCR_NOISE_MAX_NON_ALNUM_RATIO = 0.35
OCR_NOISE_MIN_WORDS = 20


@dataclass(frozen=True)
class LayoutQuality:
    status: Literal["ok", "suspect", "improved_by_ocr", "ocr_attempted_no_improvement"]
    warnings: list[str] = field(default_factory=list)
    char_count: int = 0
    word_count: int = 0
    line_count: int = 0
    avg_line_length: float = 0.0
    short_line_ratio: float = 0.0
    punctuated_line_ratio: float = 0.0
    original_char_count: int | None = None
    ocr_char_count: int | None = None
    original_word_count: int | None = None
    ocr_word_count: int | None = None

    def metadata(self) -> dict:
        return {
            "status": self.status,
            "warnings": self.warnings,
            "char_count": self.char_count,
            "word_count": self.word_count,
            "line_count": self.line_count,
            "avg_line_length": round(self.avg_line_length, 2),
            "short_line_ratio": round(self.short_line_ratio, 3),
            "punctuated_line_ratio": round(self.punctuated_line_ratio, 3),
            "original_char_count": self.original_char_count,
            "ocr_char_count": self.ocr_char_count,
            "original_word_count": self.original_word_count,
            "ocr_word_count": self.ocr_word_count,
        }


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
    extraction_source: Literal["pypdf", "ocr"] = "pypdf"
    layout_quality: LayoutQuality | None = None

    def metadata(self) -> dict:
        return {
            "page": self.page,
            "text": self.text,
            "char_count": self.char_count,
            "section_title": self.section_title,
            "extraction_source": self.extraction_source,
            "layout_quality": (
                self.layout_quality.metadata()
                if self.layout_quality
                else LayoutQuality(status="ok", char_count=self.char_count).metadata()
            ),
        }


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
    layout_quality_rules_version: str = LAYOUT_QUALITY_RULES_VERSION
    layout_quality_status: str = "ok"
    layout_suspect_pages: list[int] = field(default_factory=list)
    layout_ocr_pages_requested: list[int] = field(default_factory=list)
    layout_ocr_pages_replaced: list[int] = field(default_factory=list)
    layout_ocr_pages_kept_original: list[int] = field(default_factory=list)
    layout_warnings: list[str] = field(default_factory=list)

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
                "layout_quality_rules_version": self.layout_quality_rules_version,
                "layout_quality_status": self.layout_quality_status,
                "layout_suspect_pages": self.layout_suspect_pages,
                "layout_ocr_pages_requested": self.layout_ocr_pages_requested,
                "layout_ocr_pages_replaced": self.layout_ocr_pages_replaced,
                "layout_ocr_pages_kept_original": self.layout_ocr_pages_kept_original,
                "layout_warnings": self.layout_warnings,
            },
            "extracted_pages": [page.metadata() for page in self.extracted_pages],
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


def _text_stats(text: str) -> tuple[int, int, int, float, float, float]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    char_count = len(text)
    word_count = len(text.split())
    line_count = len(lines)
    avg_line_length = (
        sum(len(line) for line in lines) / line_count if line_count else 0.0
    )
    short_lines = [
        line for line in lines if len(line) < WEAK_LAYOUT_SHORT_LINE_CHARS
    ]
    punctuated_lines = [
        line for line in lines if line.endswith((".", "!", "?", ":", ";"))
    ]
    short_line_ratio = len(short_lines) / line_count if line_count else 0.0
    punctuated_line_ratio = (
        len(punctuated_lines) / line_count if line_count else 0.0
    )
    return (
        char_count,
        word_count,
        line_count,
        avg_line_length,
        short_line_ratio,
        punctuated_line_ratio,
    )


def _non_alnum_ratio(text: str) -> float:
    if not text:
        return 1.0
    non_alnum = sum(1 for char in text if not char.isalnum() and not char.isspace())
    return non_alnum / len(text)


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


def _is_numeric_section_title(section_title: str | None) -> bool:
    return bool(section_title and section_title.strip().isdigit())


def assess_layout_quality(text: str, section_title: str | None = None) -> LayoutQuality:
    (
        char_count,
        word_count,
        line_count,
        avg_line_length,
        short_line_ratio,
        punctuated_line_ratio,
    ) = _text_stats(text)
    warnings: list[str] = []

    if char_count < WEAK_LAYOUT_MIN_CHARS:
        warnings.append("short_text_page")
    if (
        word_count < WEAK_LAYOUT_MIN_WORDS
        and line_count >= WEAK_LAYOUT_FRAGMENTED_MIN_LINES
        and short_line_ratio >= WEAK_LAYOUT_SHORT_LINE_RATIO
        and punctuated_line_ratio <= WEAK_LAYOUT_MAX_PUNCTUATED_LINE_RATIO
    ):
        warnings.append("fragmented_lines")
    if (
        _is_numeric_section_title(section_title)
        and char_count < 900
        and short_line_ratio >= WEAK_LAYOUT_NUMERIC_TITLE_SHORT_LINE_RATIO
    ):
        warnings.append("numeric_section_title")
    if (
        avg_line_length < WEAK_LAYOUT_MIN_AVG_LINE_LENGTH
        and word_count < WEAK_LAYOUT_MIN_WORDS
        and line_count >= WEAK_LAYOUT_FRAGMENTED_MIN_LINES
        and punctuated_line_ratio <= WEAK_LAYOUT_MAX_PUNCTUATED_LINE_RATIO
    ):
        warnings.append("low_punctuation_ratio")

    return LayoutQuality(
        status="suspect" if warnings else "ok",
        warnings=warnings,
        char_count=char_count,
        word_count=word_count,
        line_count=line_count,
        avg_line_length=avg_line_length,
        short_line_ratio=short_line_ratio,
        punctuated_line_ratio=punctuated_line_ratio,
        original_char_count=char_count,
        original_word_count=word_count,
    )


def _layout_status(pages: list[ExtractedPdfPage]) -> str:
    if any(
        page.layout_quality and page.layout_quality.status == "improved_by_ocr"
        for page in pages
    ):
        return "improved_by_ocr"
    if any(page.layout_quality and page.layout_quality.status == "suspect" for page in pages):
        return "suspect"
    if any(
        page.layout_quality
        and page.layout_quality.status == "ocr_attempted_no_improvement"
        for page in pages
    ):
        return "ocr_attempted_no_improvement"
    return "ok"


def _layout_warnings(pages: list[ExtractedPdfPage]) -> list[str]:
    warnings: set[str] = set()
    for page in pages:
        if page.layout_quality:
            warnings.update(page.layout_quality.warnings)
    return sorted(warnings)


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

        section_title = _detect_section_title(text)
        extracted_pages.append(
            ExtractedPdfPage(
                page=i,
                text=text,
                char_count=len(text),
                section_title=section_title,
                extraction_source="pypdf",
                layout_quality=assess_layout_quality(text, section_title),
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

    layout_suspect_pages = [
        page.page
        for page in extracted_pages
        if page.layout_quality and page.layout_quality.status == "suspect"
    ]

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
        layout_quality_status=_layout_status(extracted_pages),
        layout_suspect_pages=layout_suspect_pages,
        layout_warnings=_layout_warnings(extracted_pages),
    )


def should_attempt_ocr(extraction: PdfExtraction) -> bool:
    if extraction.status == "failed":
        return "possible_scan_or_empty_text" in extraction.warnings
    if extraction.status != "partial" or "possible_scan_or_empty_text" not in extraction.warnings:
        return False
    if extraction.page_count == 0:
        return True
    return (
        extraction.pages_with_text == 0
        or extraction.pages_with_text / extraction.page_count < 0.5
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


def build_pages_pdf_for_ocr(path: str, pages: list[int]) -> tuple[str, dict[int, int]]:
    if not pages:
        raise ValueError("pages must not be empty")

    reader = PdfReader(path)
    writer = PdfWriter()
    page_map: dict[int, int] = {}

    for subset_page, original_page in enumerate(pages, start=1):
        if original_page < 1 or original_page > len(reader.pages):
            raise ValueError(f"Invalid page number for OCR: {original_page}")
        writer.add_page(reader.pages[original_page - 1])
        page_map[subset_page] = original_page

    digest = hashlib.sha256(f"{path}:{','.join(map(str, pages))}".encode()).hexdigest()
    subset_path = STORAGE_DIR / f"{digest}_ocr_pages_{'_'.join(map(str, pages))}.pdf"
    with subset_path.open("wb") as fh:
        writer.write(fh)

    return str(subset_path), page_map


def _looks_noisy_ocr(text: str, quality: LayoutQuality) -> bool:
    return (
        quality.word_count < OCR_NOISE_MIN_WORDS
        or quality.short_line_ratio > OCR_NOISE_MAX_SHORT_LINE_RATIO
        or _non_alnum_ratio(text) > OCR_NOISE_MAX_NON_ALNUM_RATIO
    )


def _should_replace_with_ocr(
    original: ExtractedPdfPage,
    ocr_text: str,
    ocr_section_title: str | None,
    ocr_quality: LayoutQuality,
) -> bool:
    original_quality = original.layout_quality or assess_layout_quality(
        original.text,
        original.section_title,
    )
    if _looks_noisy_ocr(ocr_text, ocr_quality):
        return False

    original_words = original_quality.word_count
    ocr_words = ocr_quality.word_count
    original_title = original.section_title or ""
    ocr_title = ocr_section_title or ""
    restores_title = (
        bool(ocr_title)
        and not _is_numeric_section_title(ocr_title)
        and (
            not original_title
            or _is_numeric_section_title(original_title)
            or len(ocr_title) > len(original_title)
        )
    )
    improves_punctuation = (
        ocr_quality.punctuated_line_ratio > original_quality.punctuated_line_ratio
        and ocr_quality.word_count >= original_quality.word_count
    )
    has_word_gain = (
        ocr_words > original_words
        and (
            original_words == 0
            or ocr_words / max(original_words, 1) >= OCR_MIN_WORD_GAIN_RATIO
        )
    )
    has_char_gain = (
        ocr_quality.char_count > original_quality.char_count
        and ocr_quality.char_count
        / max(original_quality.char_count, 1)
        >= OCR_MIN_CHAR_GAIN_RATIO
    )

    return has_word_gain or restores_title or improves_punctuation or (
        has_char_gain and ocr_words > original_words
    )


def _merge_layout_ocr_pages(
    extraction: PdfExtraction,
    ocr_result: OcrResult,
    *,
    requested_pages: list[int],
    page_map: dict[int, int],
    warnings: list[str] | None = None,
) -> PdfExtraction:
    ocr_pages_by_original: dict[int, ExtractedPdfPage] = {}
    for ocr_page in ocr_result.pages:
        original_page = page_map.get(ocr_page.page, ocr_page.page)
        text = _normalize_extracted_text(ocr_page.text)
        if not text:
            continue
        section_title = _detect_section_title(text)
        quality = assess_layout_quality(text, section_title)
        ocr_pages_by_original[original_page] = ExtractedPdfPage(
            page=original_page,
            text=text,
            char_count=len(text),
            section_title=section_title,
            extraction_source="ocr",
            layout_quality=quality,
        )

    replaced_pages: list[int] = []
    kept_original_pages: list[int] = []
    merged_pages: list[ExtractedPdfPage] = []

    for page in extraction.extracted_pages:
        if page.page not in requested_pages:
            merged_pages.append(page)
            continue

        ocr_page = ocr_pages_by_original.get(page.page)
        original_quality = page.layout_quality or assess_layout_quality(
            page.text,
            page.section_title,
        )
        if not ocr_page or not ocr_page.layout_quality:
            kept_original_pages.append(page.page)
            merged_pages.append(
                replace(
                    page,
                    layout_quality=replace(
                        original_quality,
                        status="ocr_attempted_no_improvement",
                    ),
                )
            )
            continue

        if _should_replace_with_ocr(
            page,
            ocr_page.text,
            ocr_page.section_title,
            ocr_page.layout_quality,
        ):
            replaced_pages.append(page.page)
            merged_pages.append(
                replace(
                    ocr_page,
                    layout_quality=replace(
                        ocr_page.layout_quality,
                        status="improved_by_ocr",
                        original_char_count=page.char_count,
                        ocr_char_count=ocr_page.char_count,
                        original_word_count=original_quality.word_count,
                        ocr_word_count=ocr_page.layout_quality.word_count,
                    ),
                )
            )
        else:
            kept_original_pages.append(page.page)
            merged_pages.append(
                replace(
                    page,
                    layout_quality=replace(
                        original_quality,
                        status="ocr_attempted_no_improvement",
                        ocr_char_count=ocr_page.char_count,
                        ocr_word_count=ocr_page.layout_quality.word_count,
                    ),
                )
            )

    merged_pages.sort(key=lambda page: page.page)
    raw_text = "\n\n".join(_format_page_text(page) for page in merged_pages).strip()
    layout_status = _layout_status(merged_pages)

    return replace(
        extraction,
        method=f"{extraction.method}+{ocr_result.provider}.layout_ocr",
        warnings=sorted(set([*extraction.warnings, *(warnings or [])])),
        extracted_pages=merged_pages,
        raw_text=raw_text,
        ocr_used=bool(replaced_pages),
        ocr_provider=ocr_result.provider,
        ocr_model=ocr_result.model,
        ocr_trigger_reason="weak_layout_quality",
        ocr_pages_processed=ocr_result.pages_processed,
        layout_quality_status=layout_status,
        layout_ocr_pages_requested=requested_pages,
        layout_ocr_pages_replaced=replaced_pages,
        layout_ocr_pages_kept_original=kept_original_pages,
        layout_warnings=_layout_warnings(merged_pages),
    )


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

        section_title = _detect_section_title(text)
        extracted_pages.append(
            ExtractedPdfPage(
                page=page.page,
                text=text,
                char_count=len(text),
                section_title=section_title,
                extraction_source="ocr",
                layout_quality=assess_layout_quality(text, section_title),
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
    trigger_reason = (
        "possible_scan_or_empty_text"
        if should_attempt_ocr(extraction)
        else "weak_layout_quality"
        if extraction.status == "success" and extraction.layout_suspect_pages
        else None
    )
    if not trigger_reason:
        return extraction

    if ocr_client is None or not getattr(ocr_client, "enabled", False):
        return replace(
            extraction,
            ocr_provider=getattr(ocr_client, "provider", None),
            ocr_model=getattr(ocr_client, "model", None),
            ocr_trigger_reason=trigger_reason,
        )

    if trigger_reason == "possible_scan_or_empty_text":
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

    requested_pages = extraction.layout_suspect_pages
    try:
        subset_path, page_map = build_pages_pdf_for_ocr(path, requested_pages)
        ocr_path, clean_warnings, clean_errors = clean_pdf_for_ocr(subset_path)
    except Exception as exc:
        return replace(
            extraction,
            errors=[
                *extraction.errors,
                f"layout_ocr_prepare: {exc.__class__.__name__}: {exc}",
            ],
            ocr_provider=ocr_client.provider,
            ocr_model=ocr_client.model,
            ocr_trigger_reason=trigger_reason,
            layout_ocr_pages_requested=requested_pages,
        )

    if clean_errors:
        return replace(
            extraction,
            warnings=[*extraction.warnings, *clean_warnings],
            errors=[*extraction.errors, *clean_errors],
            ocr_provider=ocr_client.provider,
            ocr_model=ocr_client.model,
            ocr_trigger_reason=trigger_reason,
            layout_ocr_pages_requested=requested_pages,
        )

    try:
        ocr_result = await ocr_client.extract_pdf(
            ocr_path,
            metadata={
                "trigger_reason": trigger_reason,
                "original_path": path,
                "ocr_pages": requested_pages,
                "page_map": page_map,
            },
        )
    except Exception as exc:
        return replace(
            extraction,
            warnings=[*extraction.warnings, *clean_warnings],
            errors=[
                *extraction.errors,
                f"layout_ocr: {exc.__class__.__name__}: {exc}",
            ],
            ocr_provider=ocr_client.provider,
            ocr_model=ocr_client.model,
            ocr_trigger_reason=trigger_reason,
            layout_ocr_pages_requested=requested_pages,
        )

    return _merge_layout_ocr_pages(
        extraction,
        ocr_result,
        requested_pages=requested_pages,
        page_map=page_map,
        warnings=clean_warnings,
    )


def extract_pdf_text(path: str) -> str:
    return extract_pdf(path).raw_text


def normalize_text(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.splitlines()).strip()
