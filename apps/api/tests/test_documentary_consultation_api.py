from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi import HTTPException

from app.api import consultation
from main import app


SOURCE_ID = UUID("10000000-0000-0000-0000-000000000001")
DOCUMENT_ID = UUID("10000000-0000-0000-0000-000000000002")
INDEX_VERSION_ID = UUID("10000000-0000-0000-0000-000000000003")
CHUNK_ID = UUID("10000000-0000-0000-0000-000000000004")
RUN_ID = UUID("10000000-0000-0000-0000-000000000005")
HIT_ID = UUID("10000000-0000-0000-0000-000000000006")


class FakeCursor:
    def __init__(self):
        self._result = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, query, params=None):
        compact_query = " ".join(query.split())
        now = datetime(2026, 6, 14, tzinfo=UTC)
        metadata = {
            "source_code": "ps",
            "theme_tags": ["ia", "service_public"],
            "visibility_scope": "public",
            "access_level": "open",
            "extraction": {"status": "success"},
            "extracted_pages": [
                {
                    "page": 1,
                    "text": "Texte page 1",
                    "char_count": 12,
                    "section_title": "Intro",
                    "extraction_source": "pypdf",
                    "layout_quality": {"status": "ok"},
                },
                {
                    "page": 2,
                    "text": "Texte page 2",
                    "char_count": 12,
                    "section_title": None,
                    "extraction_source": "ocr",
                    "layout_quality": {"status": "improved_by_ocr"},
                },
            ],
        }

        if "(SELECT COUNT(*) FROM documents)::int AS documents" in compact_query:
            self._result = {
                "documents": 3,
                "sources": 2,
                "chunks": 8,
                "runs": 5,
                "structured_objects": 1,
            }
            return

        if "FROM index_versions" in compact_query and "LIMIT 5" in compact_query:
            self._result = [
                {
                    "id": INDEX_VERSION_ID,
                    "name": "active-test",
                    "embedding_provider": "mistral",
                    "embedding_model": "mistral-embed",
                    "embedding_dimension": 1024,
                    "vector_collection": "test_collection",
                    "chunking_version": "generic_window_v1",
                    "split_strategy": "generic_window_v1",
                    "chunk_size": 450,
                    "chunk_overlap": 80,
                    "min_chunk_size": 80,
                    "max_chunk_size": 650,
                    "is_active": True,
                    "created_at": now,
                }
            ]
            return

        if "FROM index_versions" in compact_query and "COUNT(*) OVER()" in compact_query:
            self._result = [
                {
                    "id": INDEX_VERSION_ID,
                    "name": "active-test",
                    "embedding_provider": "mistral",
                    "embedding_model": "mistral-embed",
                    "embedding_dimension": 1024,
                    "vector_collection": "test_collection",
                    "chunking_version": "generic_window_v1",
                    "split_strategy": "generic_window_v1",
                    "chunk_size": 450,
                    "chunk_overlap": 80,
                    "min_chunk_size": 80,
                    "max_chunk_size": 650,
                    "is_active": True,
                    "created_at": now,
                    "total_count": 1,
                }
            ]
            return

        if "FROM index_versions" in compact_query:
            self._result = {
                "id": INDEX_VERSION_ID,
                "name": "active-test",
                "embedding_provider": "mistral",
                "embedding_model": "mistral-embed",
                "embedding_dimension": 1024,
                "vector_collection": "test_collection",
                "chunking_version": "generic_window_v1",
                "split_strategy": "generic_window_v1",
                "chunk_size": 450,
                "chunk_overlap": 80,
                "min_chunk_size": 80,
                "max_chunk_size": 650,
                "is_active": True,
                "created_at": now,
            }
            return

        if "FROM sources" in compact_query and "WHERE sources." in compact_query:
            self._result = {
                "source_id": SOURCE_ID,
                "source_code": "ps",
                "source_type": "pdf",
                "origin": "manifest",
                "author": "PS",
                "published_at": now,
                "document_count": 1,
                "chunk_count": 1,
            }
            return

        if "FROM sources" in compact_query:
            self._result = [
                {
                    "source_id": SOURCE_ID,
                    "source_code": "ps",
                    "source_type": "pdf",
                    "origin": "manifest",
                    "author": "PS",
                    "published_at": now,
                    "document_count": 1,
                    "chunk_count": 1,
                    "total_count": 1,
                }
            ]
            return

        if "COUNT(*)::int AS chunk_count" in compact_query:
            self._result = {
                "chunk_count": 1,
                "chunks_without_source_code": 0,
                "chunks_without_pages": 0,
            }
            return

        if compact_query.startswith("UPDATE index_versions"):
            self._result = None
            return

        if (
            "FROM documents" in compact_query
            and "WHERE documents.id" in compact_query
        ):
            self._result = {
                "document_id": DOCUMENT_ID,
                "source_id": SOURCE_ID,
                "source_code": "ps",
                "title": "Sample document",
                "filename": "ps.pdf",
                "mime_type": "application/pdf",
                "status": "indexed",
                "created_at": now,
                "metadata": metadata,
                "chunk_count": 1,
            }
            return

        if "FROM documents" in compact_query and "JOIN sources" in compact_query:
            self._result = [
                {
                    "document_id": DOCUMENT_ID,
                    "source_id": SOURCE_ID,
                    "source_code": "ps",
                    "title": "Sample document",
                    "filename": "ps.pdf",
                    "mime_type": "application/pdf",
                    "status": "indexed",
                    "created_at": now,
                    "metadata": metadata,
                    "chunk_count": 1,
                    "total_count": 1,
                }
            ]
            return

        if "SELECT id, title, metadata FROM documents" in compact_query:
            self._result = {
                "id": DOCUMENT_ID,
                "title": "Sample document",
                "metadata": metadata,
            }
            return

        if (
            "FROM document_chunks" in compact_query
            and "WHERE document_id" in compact_query
        ):
            self._result = [
                {
                    "chunk_id": CHUNK_ID,
                    "document_id": DOCUMENT_ID,
                    "index_version_id": INDEX_VERSION_ID,
                    "chunk_index": 0,
                    "page_start": 1,
                    "page_end": 2,
                    "token_count": 20,
                    "content": "Contenu chunk sensible pour liste",
                    "metadata": metadata,
                    "total_count": 1,
                }
            ]
            return

        if (
            "FROM document_chunks" in compact_query
            and "WHERE id" in compact_query
        ):
            self._result = {
                "chunk_id": CHUNK_ID,
                "document_id": DOCUMENT_ID,
                "index_version_id": INDEX_VERSION_ID,
                "chunk_index": 0,
                "page_start": 1,
                "page_end": 2,
                "token_count": 20,
                "content": "Contenu chunk detail",
                "metadata": metadata,
            }
            return

        if "FROM runs" in compact_query and "COUNT(*) OVER()" in compact_query:
            self._result = [
                {
                    "run_id": RUN_ID,
                    "run_type": "retrieval",
                    "status": "succeeded",
                    "index_version_id": INDEX_VERSION_ID,
                    "started_at": now,
                    "finished_at": now,
                    "total_count": 1,
                }
            ]
            return

        if "FROM runs" in compact_query and "LIMIT 5" in compact_query:
            self._result = [
                {
                    "run_id": RUN_ID,
                    "run_type": "retrieval",
                    "status": "succeeded",
                    "index_version_id": INDEX_VERSION_ID,
                    "started_at": now,
                    "finished_at": now,
                }
            ]
            return

        if "FROM runs" in compact_query:
            self._result = {
                "run_id": RUN_ID,
                "run_type": "retrieval",
                "status": "succeeded",
                "index_version_id": INDEX_VERSION_ID,
                "input": {
                    "query": "test",
                    "messages": [{"role": "user", "content": "prompt complet"}],
                    "metadata_filters": {"source_code": ["ps"]},
                },
                "output": {"hits": 1, "response_metadata": {"raw": "provider"}},
                "error": None,
                "started_at": now,
                "finished_at": now,
            }
            return

        if "FROM retrieval_hits" in compact_query:
            self._result = [
                {
                    "retrieval_hit_id": HIT_ID,
                    "run_id": RUN_ID,
                    "chunk_id": CHUNK_ID,
                    "document_id": DOCUMENT_ID,
                    "rank_initial": 2,
                    "rank_final": 1,
                    "dense_score": 0.8,
                    "lexical_score": 0.4,
                    "rerank_score": 0.95,
                    "metadata": metadata,
                    "total_count": 1,
                }
            ]
            return

        self._result = None

    def fetchone(self):
        return self._result

    def fetchall(self):
        return self._result or []


class FakeConnection:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def cursor(self):
        return FakeCursor()


def _patch_connection(monkeypatch):
    monkeypatch.setattr(consultation, "get_connection", lambda: FakeConnection())


def test_metadata_schema_exposes_registry_contract():
    response = consultation.get_metadata_schema()

    item = response.fields["document_type"]
    assert item.kind == "project_business"
    assert item.type == "enum"
    assert item.scopes == ["document", "chunk"]
    assert item.project_input == "optional"
    assert item.values_owner == "project"
    assert item.values is None
    assert item.description == "Functional category defined by the project."
    assert response.fields["source_code"].project_input == "required"
    assert response.fields["theme_tags"].project_input == "optional"
    assert response.fields["document_id"].project_input == "forbidden"


def test_chunking_strategy_catalog_exposes_canonical_strategies():
    response = consultation.get_chunking_strategy_catalog()

    items = {item.name: item for item in response.items}
    assert set(items) == {"generic_window_v1", "generic_recursive_v1"}
    assert items["generic_window_v1"].supports_structure is False
    assert items["generic_recursive_v1"].supports_structure is True
    assert items["generic_window_v1"].default_config["chunk_size"] == 450


def test_document_loader_catalog_exposes_available_loaders():
    response = consultation.get_document_loader_catalog()

    items = {item.name: item for item in response.items}
    assert set(items) == {"pdf_pypdf_ocr_v1", "plain_text_v1"}
    assert items["pdf_pypdf_ocr_v1"].ocr_supported is True
    assert items["plain_text_v1"].ocr_supported is False
    assert items["pdf_pypdf_ocr_v1"].mime_types == ["application/pdf"]
    assert "pdf" in items["pdf_pypdf_ocr_v1"].file_extensions


def test_documentary_enricher_catalog_exposes_available_enrichers():
    response = consultation.get_documentary_enricher_catalog()

    items = {item.name: item for item in response.items}
    assert set(items) == {"noop_enricher_v1"}
    assert items["noop_enricher_v1"].stages == ["pre_chunking", "post_chunking"]
    assert items["noop_enricher_v1"].enabled_by_default is False
    assert items["noop_enricher_v1"].produces_metadata is False
    assert items["noop_enricher_v1"].produces_structured_objects is False


def test_retrieval_preset_catalog_exposes_active_preset():
    response = consultation.get_retrieval_preset_catalog()

    items = {item.name: item for item in response.items}
    assert response.active_preset == "hybrid_dense_lexical_rerank_v1"
    assert set(items) == {"hybrid_dense_lexical_rerank_v1"}
    assert items["hybrid_dense_lexical_rerank_v1"].active is True
    assert items["hybrid_dense_lexical_rerank_v1"].dense_top_k == 30
    assert items["hybrid_dense_lexical_rerank_v1"].lexical_top_k == 30
    assert items["hybrid_dense_lexical_rerank_v1"].rerank_top_k == 20
    assert (
        items["hybrid_dense_lexical_rerank_v1"].reranking_strategy
        == "configured_reranker"
    )


def test_api_generic_routes_are_mounted():
    paths = {route.path for route in app.routes}

    assert "/api/search/capabilities" in paths
    assert "/api/chunking/strategies" in paths
    assert "/api/loaders" in paths
    assert "/api/enrichers" in paths
    assert "/api/retrieval/presets" in paths
    assert "/api/system/summary" in paths
    assert "/api/search" in paths
    assert "/api/documents" in paths
    assert "/api/documents/{document_id}" in paths
    assert "/api/documents/{document_id}/chunks" in paths
    assert "/api/metadata/schema" in paths
    assert "/api/runs" in paths
    assert "/api/runs/{run_id}" in paths


def test_document_command_routes_are_mounted_before_document_id_route():
    routes = [
        (route.path, set(getattr(route, "methods", set())))
        for route in app.routes
    ]
    paths = [path for path, _methods in routes]

    assert ("/api/documents/pdf", {"POST"}) in routes
    assert ("/api/documents/text", {"POST"}) in routes
    assert ("/api/index", {"POST"}) in routes
    assert (
        "/api/documents/{document_id}/chunking/preview",
        {"POST"},
    ) in routes
    assert paths.index("/api/documents/pdf") < paths.index(
        "/api/documents/{document_id}"
    )
    assert paths.index("/api/documents/text") < paths.index(
        "/api/documents/{document_id}"
    )


def test_obsolete_documentary_router_routes_are_not_mounted():
    post_routes = {
        route.path
        for route in app.routes
        if "POST" in getattr(route, "methods", set())
    }

    assert "/api/sources" not in post_routes


def test_metadata_schema_exposes_presentation_attributes():
    response = consultation.get_metadata_schema()

    theme_tags = response.fields["theme_tags"]
    assert theme_tags.presentation_group == "project"
    assert theme_tags.presentation_importance == "primary"
    assert theme_tags.presentation_widget == "tags"
    assert theme_tags.visible_in == ["ingestion", "search", "document", "catalog"]


def test_search_capabilities_distinguish_implemented_and_planned_filters():
    response = consultation.get_search_capabilities()

    implemented = set(response.implemented_filters)
    assert {"source_code", "theme_tags", "data_tags"} <= implemented
    assert response.planned_filters == []
    assert response.filter_semantics.between_fields == "AND"
    assert response.filter_semantics.within_field_values == "OR"
    assert response.filter_semantics.list_fields == [
        "data_tags",
        "theme_tags",
    ]
    assert response.filter_semantics.invalid_filters == "rejected"


def test_system_summary_aggregates_read_only_status(monkeypatch):
    _patch_connection(monkeypatch)

    response = consultation.get_system_summary()

    assert response.counts.documents == 3
    assert response.counts.sources == 2
    assert response.counts.chunks == 8
    assert response.counts.runs == 5
    assert response.counts.structured_objects == 1
    assert response.project["project_id"] == "lapythie-core"
    assert response.active_retrieval_preset == "hybrid_dense_lexical_rerank_v1"
    assert response.latest_runs[0]["run_id"] == RUN_ID
    assert response.latest_index_versions[0]["id"] == INDEX_VERSION_ID
    assert response.loaders
    assert response.enrichers
    assert response.retrieval_presets


def test_sources_catalog_is_bounded_and_sanitized(monkeypatch):
    _patch_connection(monkeypatch)

    response = consultation.list_sources(limit=10, offset=0)

    assert response.limit == 10
    assert response.total == 1
    assert response.items[0].source_code == "ps"
    assert not hasattr(response.items[0], "storage_path")
    assert not hasattr(response.items[0], "sha256")
    assert not hasattr(response.items[0], "raw_text")


def test_active_index_version_contract(monkeypatch):
    _patch_connection(monkeypatch)

    response = consultation.get_active_index_version()

    assert response.id == INDEX_VERSION_ID
    assert response.embedding_model == "mistral-embed"
    assert "api_key" not in response.model_dump_json().lower()


def test_index_versions_are_listed_with_contract(monkeypatch):
    _patch_connection(monkeypatch)

    response = consultation.list_index_versions(limit=10, offset=0)

    assert response.total == 1
    assert response.items[0].id == INDEX_VERSION_ID
    assert response.items[0].vector_collection == "test_collection"


def test_source_can_be_read_by_id_and_code(monkeypatch):
    _patch_connection(monkeypatch)

    by_id = consultation.get_source(SOURCE_ID)
    by_code = consultation.get_source_by_code("PS")

    assert by_id.source_code == "ps"
    assert by_code.source_id == SOURCE_ID


def test_documents_do_not_expose_sensitive_fields(monkeypatch):
    _patch_connection(monkeypatch)

    response = consultation.list_documents(
        limit=50,
        offset=0,
        theme_tags=None,
    )

    item = response.items[0]
    assert item.document_id == DOCUMENT_ID
    assert item.metadata["source_code"] == "ps"
    assert not hasattr(item, "raw_text")
    assert not hasattr(item, "storage_path")
    assert not hasattr(item, "sha256")
    assert "extraction" not in item.metadata
    assert "extracted_pages" not in item.metadata


def test_document_chunks_hide_content_by_default(monkeypatch):
    _patch_connection(monkeypatch)

    response = consultation.list_document_chunks(
        DOCUMENT_ID,
        limit=50,
        offset=0,
    )

    assert response.items[0].content is None
    assert response.items[0].metadata["source_code"] == "ps"


def test_document_chunks_can_include_content(monkeypatch):
    _patch_connection(monkeypatch)

    response = consultation.list_document_chunks(
        DOCUMENT_ID,
        limit=50,
        offset=0,
        include_content=True,
    )

    assert response.items[0].content == "Contenu chunk sensible pour liste"


def test_document_extraction_is_page_limited_and_can_hide_text(monkeypatch):
    _patch_connection(monkeypatch)

    response = consultation.get_document_extraction(
        DOCUMENT_ID,
        page_from=2,
        page_to=2,
        include_text=False,
    )

    assert response.total_pages == 2
    assert len(response.pages) == 1
    assert response.pages[0].page == 2
    assert response.pages[0].text is None


def test_runs_list_is_paginated_and_filterable(monkeypatch):
    _patch_connection(monkeypatch)

    response = consultation.list_runs(
        limit=25,
        offset=0,
        run_type="retrieval",
        status="succeeded",
        index_version_id=INDEX_VERSION_ID,
    )

    assert response.total == 1
    assert response.limit == 25
    assert response.items[0].run_id == RUN_ID
    assert response.items[0].run_type == "retrieval"
    assert response.items[0].status == "succeeded"


def test_run_detail_masks_prompt_and_provider_raw_payload(monkeypatch):
    _patch_connection(monkeypatch)

    response = consultation.get_run(RUN_ID)

    assert "messages" not in response.input
    assert "response_metadata" not in response.output
    assert response.input["metadata_filters"] == {"source_code": ["ps"]}


def test_retrieval_hits_expose_scores_and_safe_metadata(monkeypatch):
    _patch_connection(monkeypatch)

    response = consultation.get_run_retrieval_hits(RUN_ID, limit=50, offset=0)

    item = response.items[0]
    assert item.dense_score == 0.8
    assert item.lexical_score == 0.4
    assert item.rerank_score == 0.95
    assert item.metadata["source_code"] == "ps"
    assert "extracted_pages" not in item.metadata


def test_stable_search_facade_reuses_documentary_search_and_adds_scores(monkeypatch):
    _patch_connection(monkeypatch)

    async def fake_search(payload):
        assert payload.filters.active_filters() == {"source_code": ["ps"]}
        assert "top_k" not in payload.model_fields_set
        assert "rerank_top_k" not in payload.model_fields_set
        return SimpleNamespace(
            run_id=RUN_ID,
            hits=[
                SimpleNamespace(
                    chunk_id=CHUNK_ID,
                    document_id=DOCUMENT_ID,
                    rank=1,
                    score=0.95,
                    content="Contenu chunk",
                    metadata={
                        "source_code": "ps",
                        "extraction": {"status": "success"},
                    },
                )
            ],
        )

    monkeypatch.setattr(consultation, "documentary_search_documents", fake_search)

    response = asyncio.run(
        consultation.search_documents(
            consultation.StableSearchRequest(
                query="IA bien commun",
                index_version_id=INDEX_VERSION_ID,
                    filters=consultation.SearchMetadataFilters(source_code=["ps"]),
            )
        )
    )

    assert response.run_id == RUN_ID
    assert response.filters_applied == {"source_code": ["ps"]}
    assert response.hits[0].rank_initial == 2
    assert response.hits[0].dense_score == 0.8
    assert response.hits[0].lexical_score == 0.4
    assert response.hits[0].rerank_score == 0.95
    assert "extraction" not in response.hits[0].metadata


def test_stable_search_converts_missing_index_to_404(monkeypatch):
    async def fake_search(payload):
        raise ValueError(f"Index version not found: {payload.index_version_id}")

    monkeypatch.setattr(consultation, "documentary_search_documents", fake_search)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            consultation.search_documents(
                consultation.StableSearchRequest(
                    query="test",
                    index_version_id=INDEX_VERSION_ID,
                )
            )
        )

    assert exc_info.value.status_code == 404


def test_promote_index_version_checks_qdrant_and_updates_active(monkeypatch):
    _patch_connection(monkeypatch)

    class FakeQdrant:
        def count(self, *, collection_name, exact):
            assert collection_name == "test_collection"
            assert exact is True
            return SimpleNamespace(count=1)

    monkeypatch.setattr(consultation, "get_qdrant_client", lambda: FakeQdrant())

    response = consultation.promote_index_version(INDEX_VERSION_ID)

    assert response.index_version_id == INDEX_VERSION_ID
    assert response.is_active is True
    assert response.chunk_count == 1
    assert response.qdrant_point_count == 1


def test_promote_index_version_returns_503_when_qdrant_unavailable(monkeypatch):
    _patch_connection(monkeypatch)

    class BrokenQdrant:
        def count(self, *, collection_name, exact):
            raise RuntimeError("qdrant down")

    monkeypatch.setattr(consultation, "get_qdrant_client", lambda: BrokenQdrant())

    with pytest.raises(HTTPException) as exc_info:
        consultation.promote_index_version(INDEX_VERSION_ID)

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail["error"] == "qdrant_unavailable"
