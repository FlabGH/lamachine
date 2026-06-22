import importlib.util
import sys
from pathlib import Path


def _load_ocr_report_module():
    script_path = (
        Path(__file__).resolve().parents[3]
        / "scripts"
        / "phase3_ocr_quality_report.py"
    )
    spec = importlib.util.spec_from_file_location("phase3_ocr_quality_report", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_summarize_document_ocr_quality_extracts_core_metrics():
    module = _load_ocr_report_module()
    row = {
        "id": "doc-1",
        "title": "Document OCR",
        "metadata": {
            "source_code": "ps",
            "extraction": {
                "status": "success",
                "ocr_used": True,
                "page_count": 3,
                "layout_quality_status": "improved_by_ocr",
                "layout_suspect_pages": [2],
                "layout_ocr_pages_replaced": [2],
                "layout_ocr_pages_kept_original": [1],
                "errors": ["warning-like error"],
            },
            "extracted_pages": [
                {"page": 1, "extraction_source": "pypdf"},
                {"page": 2, "extraction_source": "ocr"},
            ],
        },
    }

    summary = module.summarize_document_ocr_quality(row)

    assert summary.document_id == "doc-1"
    assert summary.source_code == "ps"
    assert summary.extraction_status == "success"
    assert summary.ocr_used is True
    assert summary.page_count == 3
    assert summary.layout_quality_status == "improved_by_ocr"
    assert summary.ocr_pages == [2]
    assert summary.suspect_pages == [2]
    assert summary.replaced_pages == [2]
    assert summary.kept_original_pages == [1]
    assert summary.errors == ["warning-like error"]


def test_summarize_corpus_quality_computes_rates():
    module = _load_ocr_report_module()
    documents = [
        module.DocumentOcrQuality(
            document_id="doc-1",
            title="A",
            source_code="a",
            extraction_status="success",
            ocr_used=True,
            page_count=4,
            layout_quality_status="improved_by_ocr",
            ocr_pages=[2],
            suspect_pages=[2],
            replaced_pages=[2],
            kept_original_pages=[],
            errors=[],
        ),
        module.DocumentOcrQuality(
            document_id="doc-2",
            title="B",
            source_code="b",
            extraction_status="partial",
            ocr_used=False,
            page_count=2,
            layout_quality_status="suspect",
            ocr_pages=[],
            suspect_pages=[1],
            replaced_pages=[],
            kept_original_pages=[1],
            errors=["ocr failed"],
        ),
    ]

    summary = module.summarize_corpus_quality(documents)

    assert summary["total_documents"] == 2
    assert summary["ocr_used_documents"] == 1
    assert summary["documents_with_errors"] == 1
    assert summary["total_pages"] == 6
    assert summary["total_ocr_pages"] == 1
    assert summary["ocr_page_rate"] == 1 / 6


def test_summarize_corpus_quality_handles_empty_input():
    module = _load_ocr_report_module()

    assert module.summarize_corpus_quality([])["ocr_page_rate"] == 0.0
