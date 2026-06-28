import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace


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
