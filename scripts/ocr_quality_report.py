#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(os.getenv("LAPYTHIE_REPO_ROOT", Path(__file__).resolve().parents[1]))
API_ROOT = Path(os.getenv("LAPYTHIE_API_ROOT", REPO_ROOT / "apps" / "api"))
DEFAULT_REPORT = REPO_ROOT / "artifacts" / "ocr_quality_report.md"
DEFAULT_JSON_REPORT = REPO_ROOT / "artifacts" / "ocr_quality_report.json"


@dataclass(frozen=True)
class DocumentOcrQuality:
    document_id: str
    title: str
    source_code: str | None
    extraction_status: str | None
    ocr_used: bool
    page_count: int
    layout_quality_status: str | None
    ocr_pages: list[int]
    suspect_pages: list[int]
    replaced_pages: list[int]
    kept_original_pages: list[int]
    errors: list[str]


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _normalize_local_service_urls() -> None:
    if Path("/.dockerenv").exists():
        return

    database_url = os.environ.get("DATABASE_URL", "")
    if "@postgres:" in database_url:
        os.environ["DATABASE_URL"] = database_url.replace("@postgres:", "@localhost:")


def _configure_imports() -> None:
    sys.path.insert(0, str(API_ROOT))


def _int_list(value: Any) -> list[int]:
    if not isinstance(value, list):
        return []
    result = []
    for item in value:
        if isinstance(item, int):
            result.append(item)
    return result


def summarize_document_ocr_quality(row: dict[str, Any]) -> DocumentOcrQuality:
    metadata = row.get("metadata") or {}
    extraction = metadata.get("extraction") or {}
    pages = metadata.get("extracted_pages") or []
    if not isinstance(extraction, dict):
        extraction = {}
    if not isinstance(pages, list):
        pages = []

    ocr_pages = sorted(
        page.get("page")
        for page in pages
        if isinstance(page, dict)
        and page.get("extraction_source") == "ocr"
        and isinstance(page.get("page"), int)
    )

    return DocumentOcrQuality(
        document_id=str(row["id"]),
        title=str(row["title"]),
        source_code=metadata.get("source_code"),
        extraction_status=extraction.get("status"),
        ocr_used=bool(extraction.get("ocr_used", False)),
        page_count=int(extraction.get("page_count") or 0),
        layout_quality_status=extraction.get("layout_quality_status"),
        ocr_pages=ocr_pages,
        suspect_pages=_int_list(extraction.get("layout_suspect_pages")),
        replaced_pages=_int_list(extraction.get("layout_ocr_pages_replaced")),
        kept_original_pages=_int_list(
            extraction.get("layout_ocr_pages_kept_original")
        ),
        errors=[
            str(error)
            for error in extraction.get("errors", [])
            if isinstance(error, str)
        ],
    )


def summarize_corpus_quality(documents: list[DocumentOcrQuality]) -> dict[str, Any]:
    total = len(documents)
    if total == 0:
        return {
            "total_documents": 0,
            "ocr_used_documents": 0,
            "documents_with_errors": 0,
            "total_pages": 0,
            "total_ocr_pages": 0,
            "ocr_page_rate": 0.0,
        }

    total_pages = sum(document.page_count for document in documents)
    total_ocr_pages = sum(len(document.ocr_pages) for document in documents)
    return {
        "total_documents": total,
        "ocr_used_documents": sum(1 for document in documents if document.ocr_used),
        "documents_with_errors": sum(1 for document in documents if document.errors),
        "total_pages": total_pages,
        "total_ocr_pages": total_ocr_pages,
        "ocr_page_rate": (
            0.0 if total_pages == 0 else total_ocr_pages / total_pages
        ),
    }


def _fetch_documents() -> list[DocumentOcrQuality]:
    from app.db import get_connection

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, title, metadata
                FROM documents
                ORDER BY created_at, id
                """
            )
            return [
                summarize_document_ocr_quality(dict(row))
                for row in cur.fetchall()
            ]


def _write_reports(
    *,
    report_path: Path,
    json_report_path: Path,
    documents: list[DocumentOcrQuality],
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    json_report_path.parent.mkdir(parents=True, exist_ok=True)
    summary = summarize_corpus_quality(documents)
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "summary": summary,
        "documents": [
            {
                "document_id": document.document_id,
                "title": document.title,
                "source_code": document.source_code,
                "extraction_status": document.extraction_status,
                "ocr_used": document.ocr_used,
                "page_count": document.page_count,
                "layout_quality_status": document.layout_quality_status,
                "ocr_pages": document.ocr_pages,
                "suspect_pages": document.suspect_pages,
                "replaced_pages": document.replaced_pages,
                "kept_original_pages": document.kept_original_pages,
                "errors": document.errors,
            }
            for document in documents
        ],
    }
    json_report_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lines = [
        "# OCR Quality Report",
        "",
        f"Generated at: `{payload['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- Total documents: {summary['total_documents']}",
        f"- Documents with OCR used: {summary['ocr_used_documents']}",
        f"- Documents with extraction errors: {summary['documents_with_errors']}",
        f"- Total pages: {summary['total_pages']}",
        f"- OCR pages: {summary['total_ocr_pages']}",
        f"- OCR page rate: {summary['ocr_page_rate']:.3f}",
        "",
        "## Documents",
        "",
        "| source_code | title | status | ocr_used | pages | ocr_pages | suspect | replaced | kept_original | errors |",
        "|---|---|---|---:|---:|---|---|---|---|---|",
    ]
    for document in documents:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(document.source_code or ""),
                    document.title.replace("|", "\\|"),
                    str(document.extraction_status or ""),
                    "yes" if document.ocr_used else "no",
                    str(document.page_count),
                    ", ".join(map(str, document.ocr_pages)),
                    ", ".join(map(str, document.suspect_pages)),
                    ", ".join(map(str, document.replaced_pages)),
                    ", ".join(map(str, document.kept_original_pages)),
                    "; ".join(document.errors).replace("|", "\\|"),
                ]
            )
            + " |"
        )
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Write OCR quality report.")
    parser.add_argument("--report", default=str(DEFAULT_REPORT.relative_to(REPO_ROOT)))
    parser.add_argument(
        "--json-report",
        default=str(DEFAULT_JSON_REPORT.relative_to(REPO_ROOT)),
    )
    args = parser.parse_args()

    _load_dotenv(REPO_ROOT / ".env")
    _normalize_local_service_urls()
    _configure_imports()

    report_path = Path(args.report)
    if not report_path.is_absolute():
        report_path = REPO_ROOT / report_path
    json_report_path = Path(args.json_report)
    if not json_report_path.is_absolute():
        json_report_path = REPO_ROOT / json_report_path

    documents = _fetch_documents()
    _write_reports(
        report_path=report_path,
        json_report_path=json_report_path,
        documents=documents,
    )
    print(report_path)
    print(json_report_path)


if __name__ == "__main__":
    main()
