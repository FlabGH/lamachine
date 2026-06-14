import importlib.util
import sys
from pathlib import Path


def _load_eval_module():
    script_path = Path(__file__).resolve().parents[3] / "scripts" / "phase3_retrieval_eval.py"
    spec = importlib.util.spec_from_file_location("phase3_retrieval_eval", script_path)
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
