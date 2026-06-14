from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

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
            "role_documentaire": "doctrine_alliee",
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

        if "FROM index_versions" in compact_query:
            self._result = {
                "id": INDEX_VERSION_ID,
                "name": "active-test",
                "embedding_provider": "mistral",
                "embedding_model": "mistral-embed",
                "embedding_dimension": 1024,
                "vector_collection": "test_collection",
                "chunking_version": "word_window_v1",
                "split_strategy": "word_window",
                "chunk_size": 450,
                "chunk_overlap": 80,
                "min_chunk_size": 80,
                "max_chunk_size": 650,
                "is_active": True,
                "created_at": now,
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

        if (
            "FROM documents" in compact_query
            and "WHERE documents.id" in compact_query
        ):
            self._result = {
                "document_id": DOCUMENT_ID,
                "source_id": SOURCE_ID,
                "source_code": "ps",
                "title": "Programme PS IA",
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
                    "title": "Programme PS IA",
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
                "title": "Programme PS IA",
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


def test_metadata_catalog_exposes_registry_contract():
    response = consultation.get_metadata_catalog(retrieval_filterable=True)

    item = next(
        item for item in response.items
        if item.metadata == "role_documentaire"
    )
    assert item.implementation_status == "implemented"
    assert "doctrine_alliee" in item.allowed_values
    assert item.deprecated is False
    assert not hasattr(item, "storage_path")


def test_api_v1_alias_is_mounted():
    paths = {route.path for route in app.routes}

    assert "/v1/search/capabilities" in paths
    assert "/api/v1/search/capabilities" in paths


def test_search_capabilities_distinguish_implemented_and_planned_filters():
    response = consultation.get_search_capabilities()

    implemented = {
        item.metadata for item in response.implemented_filters
    }
    planned = {item.metadata for item in response.planned_filters}
    assert {"source_code", "role_documentaire", "theme_tags"} <= implemented
    assert "publication_date" in planned
    assert response.filter_semantics.between_fields == "AND"
    assert response.filter_semantics.within_field_values == "OR"
    assert response.filter_semantics.list_fields == [
        "data_tags",
        "service_ids",
        "theme_tags",
    ]
    assert response.filter_semantics.invalid_filters == "rejected"


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
