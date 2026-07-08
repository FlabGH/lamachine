import asyncio

from app.api.documentary import (
    LEXICAL_SEARCH_TEXT_SQL,
    SearchMetadataFilters,
    SearchRequest,
    _build_metadata_filter_sql,
    _build_qdrant_search_filter,
    _build_lexical_websearch_query,
    _significant_lexical_terms,
    _validate_search_filters_or_422,
    search_documents,
)
import pytest
from fastapi import HTTPException

from app.services.documentary.metadata_registry import get_metadata_registry


INDEX_VERSION_ID = "00000000-0000-0000-0000-000000000000"


def test_significant_lexical_terms_filters_short_words_and_stopwords():
    terms = _significant_lexical_terms(
        "Quelle est la position de LFI sur la souveraineté numérique ?"
    )

    assert terms == ["position", "lfi", "souveraineté", "numérique"]


def test_build_lexical_websearch_query_uses_or_terms_for_tolerant_recall():
    lexical_query = _build_lexical_websearch_query(
        "Quels retards la France accuse-t-elle dans la transformation de l’action publique par l’IA ?"
    )

    assert lexical_query == (
        "retards OR france OR accuse OR transformation OR action OR publique"
    )


def test_build_lexical_websearch_query_returns_none_without_significant_term():
    assert _build_lexical_websearch_query("le de à ou ?") is None


def test_lexical_search_text_includes_documentary_metadata_fields():
    assert "content" in LEXICAL_SEARCH_TEXT_SQL
    assert "source_code" in LEXICAL_SEARCH_TEXT_SQL
    assert "title" in LEXICAL_SEARCH_TEXT_SQL
    assert "section_title" in LEXICAL_SEARCH_TEXT_SQL
    assert "theme_tags" in LEXICAL_SEARCH_TEXT_SQL


def test_search_request_uses_retrieval_defaults(monkeypatch):
    monkeypatch.delenv("DOCUMENTARY_SEARCH_TOP_K", raising=False)
    monkeypatch.delenv("DOCUMENTARY_RERANK_TOP_K", raising=False)

    request = SearchRequest(query="test", index_version_id=INDEX_VERSION_ID)

    assert request.top_k == 30
    assert request.rerank_top_k == 20
    assert request.filters is None
    assert request.preset is None


def test_search_request_defaults_are_configurable_from_env(monkeypatch):
    monkeypatch.setenv("DOCUMENTARY_SEARCH_TOP_K", "12")
    monkeypatch.setenv("DOCUMENTARY_RERANK_TOP_K", "7")

    request = SearchRequest(query="test", index_version_id=INDEX_VERSION_ID)

    assert request.top_k == 12
    assert request.rerank_top_k == 7


def test_search_metadata_filters_preserve_generic_filter_payload():
    filters = SearchMetadataFilters(
        source_code=["ps"],
        language=["fr"],
    )

    assert filters.active_filters() == {
        "source_code": ["ps"],
        "language": ["fr"],
    }


def test_search_metadata_filters_reject_invalid_value_against_registry():
    with pytest.raises(HTTPException) as exc_info:
        _validate_search_filters_or_422(SearchMetadataFilters(language=["de"]))

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail["issues"][0]["code"] == "invalid_enum_value"


def test_search_rejects_unfilterable_field_before_accessing_dependencies():
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            search_documents(
                SearchRequest(
                    query="test",
                    index_version_id=INDEX_VERSION_ID,
                    filters=SearchMetadataFilters(title=["Document"]),
                )
            )
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail["issues"][0]["code"] == "filter_not_allowed"


def test_build_qdrant_search_filter_uses_payload_fields():
    qdrant_filter = _build_qdrant_search_filter(
        {"source_code": ["ps"], "theme_tags": ["ia"]}
    )

    assert qdrant_filter is not None
    assert [condition.key for condition in qdrant_filter.must] == [
        "source_code",
        "theme_tags",
    ]
    assert qdrant_filter.must[0].match.any == ["ps"]
    assert qdrant_filter.must[1].match.any == ["ia"]


def test_build_metadata_filter_sql_handles_scalar_and_array_fields():
    sql, params = _build_metadata_filter_sql(
        {"source_code": ["ps"], "theme_tags": ["ia", "service_public"]},
        metadata_expression="document_chunks.metadata",
        registry=get_metadata_registry(),
    )

    assert "document_chunks.metadata @> %s::jsonb" in sql
    assert "(document_chunks.metadata->%s) ?| %s" in sql
    assert params == [
        '{"source_code": "ps"}',
        "theme_tags",
        ["ia", "service_public"],
    ]
