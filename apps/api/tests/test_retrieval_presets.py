import pytest
from pydantic import ValidationError

from app.services.documentary.metadata_validation import MetadataValidationError
from app.services.documentary import retrieval_presets
from app.services.documentary.retrieval_presets import (
    RetrievalPreset,
    RerankingStrategy,
    load_retrieval_preset_catalog,
    resolve_retrieval_plan,
)


def test_default_retrieval_preset_catalog_loads():
    catalog = load_retrieval_preset_catalog()

    preset = catalog.presets["hybrid_dense_lexical_rerank_v1"]
    assert preset.name == "hybrid_dense_lexical_rerank_v1"
    assert preset.dense_top_k == 30
    assert preset.lexical_top_k == 30
    assert preset.rerank_top_k == 20
    assert preset.reranking_strategy is RerankingStrategy.configured_reranker
    assert preset.filters == {}


def test_retrieval_preset_catalog_rejects_mismatched_names(tmp_path):
    catalog_path = tmp_path / "retrieval_presets.yaml"
    catalog_path.write_text(
        "\n".join(
            [
                "presets:",
                "  expected_name:",
                "    name: other_name",
                "    description: Invalid preset",
                "    dense_top_k: 10",
                "    lexical_top_k: 10",
                "    rerank_top_k: 5",
                "    reranking_strategy: configured_reranker",
                "    filters: {}",
                "    trace_parameters: {}",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValidationError):
        load_retrieval_preset_catalog(catalog_path)


def test_retrieval_preset_catalog_rejects_invalid_filter(tmp_path):
    catalog_path = tmp_path / "retrieval_presets.yaml"
    catalog_path.write_text(
        "\n".join(
            [
                "presets:",
                "  invalid_filter_v1:",
                "    name: invalid_filter_v1",
                "    description: Invalid preset",
                "    dense_top_k: 10",
                "    lexical_top_k: 10",
                "    rerank_top_k: 5",
                "    reranking_strategy: configured_reranker",
                "    filters:",
                "      title: [Document]",
                "    trace_parameters: {}",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValidationError) as exc_info:
        load_retrieval_preset_catalog(catalog_path)

    assert "Field is not enabled for retrieval filtering" in str(exc_info.value)


def test_get_retrieval_preset_uses_project_default(monkeypatch):
    retrieval_presets.get_retrieval_preset_catalog.cache_clear()

    preset = retrieval_presets.get_retrieval_preset()

    assert preset.name == "hybrid_dense_lexical_rerank_v1"

    retrieval_presets.get_retrieval_preset_catalog.cache_clear()


def test_resolve_retrieval_plan_uses_preset_values_by_default():
    plan = resolve_retrieval_plan(
        requested_preset=None,
        request_fields={"query", "index_version_id"},
        request_top_k=99,
        request_rerank_top_k=88,
        request_filters={},
    )

    assert plan.preset.name == "hybrid_dense_lexical_rerank_v1"
    assert plan.preset_source == "project_config"
    assert plan.dense_top_k == 30
    assert plan.lexical_top_k == 30
    assert plan.rerank_top_k == 20
    assert plan.filters == {}


def test_resolve_retrieval_plan_allows_request_top_k_override():
    plan = resolve_retrieval_plan(
        requested_preset=None,
        request_fields={"query", "index_version_id", "top_k"},
        request_top_k=12,
        request_rerank_top_k=88,
        request_filters={},
    )

    assert plan.dense_top_k == 12
    assert plan.lexical_top_k == 12
    assert plan.rerank_top_k == 20


def test_resolve_retrieval_plan_merges_non_conflicting_filters(monkeypatch):
    preset = RetrievalPreset(
        name="filtered_v1",
        description="Filtered preset",
        dense_top_k=10,
        lexical_top_k=10,
        rerank_top_k=5,
        reranking_strategy=RerankingStrategy.configured_reranker,
        filters={"language": ["fr"]},
        trace_parameters={},
    )
    monkeypatch.setattr(
        retrieval_presets,
        "get_retrieval_preset",
        lambda name=None: preset,
    )

    plan = resolve_retrieval_plan(
        requested_preset="filtered_v1",
        request_fields={"query", "index_version_id"},
        request_top_k=30,
        request_rerank_top_k=20,
        request_filters={"source_code": ["ps"]},
    )

    assert plan.preset_source == "request"
    assert plan.filters == {
        "language": ["fr"],
        "source_code": ["ps"],
    }


def test_resolve_retrieval_plan_rejects_filter_conflict(monkeypatch):
    preset = RetrievalPreset(
        name="filtered_v1",
        description="Filtered preset",
        dense_top_k=10,
        lexical_top_k=10,
        rerank_top_k=5,
        reranking_strategy=RerankingStrategy.configured_reranker,
        filters={"language": ["fr"]},
        trace_parameters={},
    )
    monkeypatch.setattr(
        retrieval_presets,
        "get_retrieval_preset",
        lambda name=None: preset,
    )

    with pytest.raises(MetadataValidationError) as exc_info:
        resolve_retrieval_plan(
            requested_preset="filtered_v1",
            request_fields={"query", "index_version_id"},
            request_top_k=30,
            request_rerank_top_k=20,
            request_filters={"language": ["en"]},
        )

    assert exc_info.value.issues[0].code == "filter_conflict"
