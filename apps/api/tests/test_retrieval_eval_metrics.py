import asyncio
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID


def _load_eval_module():
    script_path = Path(__file__).resolve().parents[3] / "scripts" / "retrieval_eval.py"
    spec = importlib.util.spec_from_file_location("retrieval_eval", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_normalize_expected_pages_accepts_ints_and_ranges():
    module = _load_eval_module()

    assert module._normalize_expected_pages([1, "3-5", "7"]) == {1, 3, 4, 5, 7}


def test_page_hit_at_matches_overlapping_page_range():
    module = _load_eval_module()
    results = [
        {"rank": 1, "page_start": 1, "page_end": 2},
        {"rank": 2, "page_start": 4, "page_end": 6},
    ]

    assert module._page_hit_at(results, {5}, 5) is True
    assert module._page_hit_at(results, {3}, 5) is False


def test_page_hit_at_is_true_without_expected_pages():
    module = _load_eval_module()

    assert module._page_hit_at([], set(), 5) is True


def test_page_coverage_rate_counts_hits_with_complete_page_range():
    module = _load_eval_module()
    results = [
        {"page_start": 1, "page_end": 1},
        {"page_start": None, "page_end": 2},
        {"page_start": 3, "page_end": 4},
    ]

    assert module._page_coverage_rate(results, 10) == 2 / 3


def test_average_returns_zero_for_empty_values():
    module = _load_eval_module()

    assert module._average([]) == 0.0
    assert module._average([10.0, 20.0]) == 15.0


def test_write_report_includes_retrieval_preset(tmp_path):
    module = _load_eval_module()
    report_path = tmp_path / "report.md"

    module._write_report(
        report_path=report_path,
        manifest_path=module.REPO_ROOT / "corpus" / "poc_ia" / "manifest.yaml",
        queries_path=module.REPO_ROOT / "corpus" / "poc_ia" / "evaluation_queries.yaml",
        index_version_id=UUID("00000000-0000-0000-0000-000000000001"),
        vector_collection="test_collection",
        query_reports=[
            {
                "query": module.QuerySpec(
                    query_id="q1",
                    query="Question",
                    intent="test",
                    expected_source_codes={"source"},
                    expected_document_ids=set(),
                    expected_theme_tags=set(),
                    expected_pages=set(),
                ),
                "results": [],
                "source_hit": False,
                "document_hit": False,
                "page_hit": True,
                "source_mrr": 0.0,
                "document_mrr": 0.0,
                "page_coverage_rate": 0.0,
                "latency_ms": 12.0,
            }
        ],
        chunk_metrics={
            "total_chunks": 0,
            "missing_source_code_rate": 0.0,
            "missing_page_range_rate": 0.0,
        },
        top_k=5,
        rerank_top_k=3,
        retrieval_preset="eval_v1",
    )

    assert "Retrieval preset: `eval_v1`" in report_path.read_text(encoding="utf-8")


def test_chunking_config_from_args_uses_canonical_strategy_defaults():
    module = _load_eval_module()
    module._configure_imports()

    default_config = module._chunking_config_from_args(
        SimpleNamespace(
            split_strategy="generic_window_v1",
            chunking_version=None,
            chunk_size=450,
            chunk_overlap=80,
            min_chunk_size=80,
            max_chunk_size=650,
        )
    )
    structural_config = module._chunking_config_from_args(
        SimpleNamespace(
            split_strategy="generic_recursive_v1",
            chunking_version=None,
            chunk_size=450,
            chunk_overlap=80,
            min_chunk_size=80,
            max_chunk_size=650,
        )
    )

    assert default_config.split_strategy == "generic_window_v1"
    assert default_config.chunking_version == "generic_window_v1"
    assert structural_config.split_strategy == "generic_recursive_v1"
    assert structural_config.chunking_version == "generic_recursive_v1"


def test_ingest_document_uses_pdf_loader(monkeypatch, tmp_path):
    module = _load_eval_module()
    module._configure_imports()

    from app.services.ai import factory
    from app.services.documentary import ingestion, loaders

    executions = []

    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, query, params=None):
            executions.append((query, params))

        def fetchone(self):
            query = executions[-1][0]
            if "INSERT INTO sources" in query:
                return {"id": UUID("00000000-0000-0000-0000-000000000001")}
            if "INSERT INTO documents" in query:
                return {"id": UUID("00000000-0000-0000-0000-000000000002")}
            return {}

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def cursor(self):
            return FakeCursor()

    class FakeTrace:
        def metadata(self):
            return {
                "name": "pdf_pypdf_ocr_v1",
                "version": "1",
                "mime_type": "application/pdf",
                "file_extension": "pdf",
                "status": "success",
                "warnings": [],
                "errors": [],
                "ocr_used": False,
                "ocr_provider": None,
                "ocr_model": None,
            }

    class FakeLoaderResult:
        raw_text = "Texte charge par loader"
        status = "success"
        trace = FakeTrace()

        def metadata(self):
            return {
                "loader": self.trace.metadata(),
                "extraction": {
                    "method": "pdf_pypdf_ocr_v1",
                    "status": "success",
                    "warnings": [],
                    "errors": [],
                    "ocr_used": False,
                },
                "extracted_pages": [],
            }

    class FakeLoader:
        async def load(self, input):
            assert input.path == "/tmp/runner.pdf"
            assert input.filename == "runner.pdf"
            assert input.ocr_client == "ocr"
            return FakeLoaderResult()

    file_path = tmp_path / "runner.pdf"
    file_path.write_bytes(b"%PDF runner")

    monkeypatch.setattr(
        ingestion,
        "save_uploaded_file",
        lambda filename, content: ("/tmp/runner.pdf", "digest"),
    )
    monkeypatch.setattr(factory, "get_ocr_client", lambda: "ocr")
    monkeypatch.setattr(loaders, "get_loader", lambda name: FakeLoader())
    monkeypatch.setattr("app.db.get_connection", lambda: FakeConnection())

    document_id = asyncio.run(
        module._ingest_document(
            {
                "file_path": file_path,
                "metadata": {
                    "title": "Runner PDF",
                    "source_code": "runner",
                },
            }
        )
    )

    assert document_id == UUID("00000000-0000-0000-0000-000000000002")
    document_inserts = [
        params for query, params in executions if "INSERT INTO documents" in query
    ]
    assert document_inserts[0][-2] == "Texte charge par loader"
    run_inserts = [
        params for query, params in executions if "INSERT INTO runs" in query
    ]
    input_payload = json.loads(run_inserts[0][2])
    output_payload = json.loads(run_inserts[0][3])
    assert input_payload["loader"]["name"] == "pdf_pypdf_ocr_v1"
    assert output_payload["loader"]["name"] == "pdf_pypdf_ocr_v1"


def test_load_queries_uses_canonical_expectations_without_roles(tmp_path):
    module = _load_eval_module()
    queries_path = tmp_path / "queries.yaml"
    queries_path.write_text(
        """
queries:
  - id: source_only
    query: Find the source
    expected_source_codes: [example]
    expected_theme_tags: [documentation]
""".strip(),
        encoding="utf-8",
    )

    queries = module._load_queries(queries_path)

    assert queries[0].expected_source_codes == {"example"}
    assert queries[0].expected_theme_tags == {"documentation"}
    assert not hasattr(queries[0], "expected_roles")


def test_validate_manifest_uses_filename_as_title_fallback(tmp_path):
    module = _load_eval_module()
    module._configure_imports()
    files_dir = tmp_path / "files"
    files_dir.mkdir()
    (files_dir / "document.pdf").write_bytes(b"%PDF")
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(
        """
documents:
  - file: document.pdf
    source_code: example
""".strip(),
        encoding="utf-8",
    )

    documents = module._validate_manifest(manifest, files_dir)

    assert documents[0]["metadata"]["title"] == "document.pdf"
    assert documents[0]["metadata"]["source_code"] == "example"


def test_validate_manifest_rejects_forbidden_project_input(tmp_path):
    module = _load_eval_module()
    module._configure_imports()
    files_dir = tmp_path / "files"
    files_dir.mkdir()
    (files_dir / "document.pdf").write_bytes(b"%PDF")
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(
        """
documents:
  - file: document.pdf
    source_code: example
    document_id: doc-1
""".strip(),
        encoding="utf-8",
    )

    try:
        module._validate_manifest(manifest, files_dir)
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("manifest validation should have failed")

    assert "document_id" in message
    assert "controlled by the system" in message


def test_validate_manifest_rejects_missing_required_project_input(tmp_path):
    module = _load_eval_module()
    module._configure_imports()
    files_dir = tmp_path / "files"
    files_dir.mkdir()
    (files_dir / "document.pdf").write_bytes(b"%PDF")
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(
        """
documents:
  - file: document.pdf
""".strip(),
        encoding="utf-8",
    )

    try:
        module._validate_manifest(manifest, files_dir)
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("manifest validation should have failed")

    assert "source_code" in message
    assert "Required field is missing" in message
