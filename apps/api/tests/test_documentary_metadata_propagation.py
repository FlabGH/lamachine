import asyncio
import json
from types import SimpleNamespace
from uuid import UUID

import pytest

from app.api import documentary
from app.services.ai.clients import EmbeddingResult, RerankResult
from app.services.documentary.enrichers import EnricherConfig, EnrichmentStage
from app.services.documentary.metadata_validation import MetadataValidationError


SOURCE_ID = UUID("00000000-0000-0000-0000-000000000101")
DOCUMENT_ID = UUID("00000000-0000-0000-0000-000000000102")
INDEX_VERSION_ID = UUID("00000000-0000-0000-0000-000000000103")
RUN_ID = UUID("00000000-0000-0000-0000-000000000104")
MODEL_CALL_ID = UUID("00000000-0000-0000-0000-000000000105")
RERANK_MODEL_CALL_ID = UUID("00000000-0000-0000-0000-000000000106")
CHUNK_ID = UUID("00000000-0000-0000-0000-000000000107")


DOCUMENT_METADATA = {
    "title": "Document metadata",
    "source_code": "metadata_source",
    "source_id": str(SOURCE_ID),
    "document_id": str(DOCUMENT_ID),
    "mime_type": "text/plain",
    "data_tags": ["interne", "juridique"],
    "visibility_scope": "organization",
    "organization_id": "org-test",
    "access_level": "restricted",
    "source_url": "https://example.test/document",
    "publication_date": "2026-06-01",
    "collected_at": "2026-06-02T10:00:00+00:00",
    "freshness_status": "current",
    "language": "fr",
    "geographic_scope": "France",
    "temporal_scope": "2025-2026",
    "is_primary_source": True,
    "citation_policy": "citable",
    "rights_status": "internal",
}


class FakeEmbeddingClient:
    provider = "fake_embedding"
    model = "fake-embedding"
    dimension = 3

    async def embed_texts(self, texts, *, metadata=None):
        return EmbeddingResult(
            vectors=[[1.0, 0.0, 0.0] for _ in texts],
            provider=self.provider,
            model=self.model,
            dimension=self.dimension,
            raw={"texts": len(texts), "metadata": metadata or {}},
        )


class FakeReranker:
    provider = "fake_reranker"
    model = "fake-reranker"

    async def rerank(self, query, candidates, *, top_k=None, metadata=None):
        return [
            RerankResult(id=candidate.id, score=0.99, rank=rank)
            for rank, candidate in enumerate(candidates[:top_k], start=1)
        ]


class FakeCursor:
    def __init__(self, state):
        self.state = state
        self._result = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, query, params=None):
        self.state["queries"].append((query, params))
        compact_query = " ".join(query.split())

        if compact_query.startswith("SELECT documents.id"):
            self._result = {
                "id": DOCUMENT_ID,
                "source_id": SOURCE_ID,
                "title": "Document metadata",
                "raw_text": (
                    "[PAGE 2] [SECTION Metadata] Les metadata enrichies doivent "
                    "etre conservees dans les chunks et les hits de recherche."
                ),
                "document_metadata": DOCUMENT_METADATA,
                "source_code": "metadata_source",
            }
            return

        if compact_query.startswith("SELECT * FROM index_versions"):
            self._result = {
                "id": INDEX_VERSION_ID,
                "embedding_dimension": 3,
                "vector_collection": "metadata_propagation_test",
                "chunk_size": 80,
                "chunk_overlap": 10,
                "split_strategy": "generic_window_v1",
                "min_chunk_size": 1,
                "max_chunk_size": 120,
                "chunking_version": "generic_window_v1",
            }
            return

        if compact_query.startswith("INSERT INTO runs"):
            self._result = {"id": RUN_ID}
            return

        if compact_query.startswith("INSERT INTO model_calls"):
            if "'reranking'" in compact_query:
                self._result = {"id": RERANK_MODEL_CALL_ID}
            else:
                self._result = {"id": MODEL_CALL_ID}
            return

        if compact_query.startswith("INSERT INTO document_chunks"):
            metadata = json.loads(params[-1])
            self.state["chunk_rows"][str(CHUNK_ID)] = {
                "id": CHUNK_ID,
                "document_id": DOCUMENT_ID,
                "content": params[4],
                "metadata": metadata,
            }
            self._result = {"id": CHUNK_ID}
            return

        if compact_query.startswith("SELECT id, document_id, content, metadata"):
            requested_ids = {str(item) for item in params[0]}
            self._result = [
                row
                for chunk_id, row in self.state["chunk_rows"].items()
                if chunk_id in requested_ids
            ]
            return

        if "lexical_chunks AS" in compact_query:
            self._result = []
            return

        self._result = None

    def fetchone(self):
        return self._result

    def fetchall(self):
        return self._result or []


class FakeConnection:
    def __init__(self, state):
        self.state = state

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def cursor(self):
        return FakeCursor(self.state)


def test_metadata_propagates_from_document_to_chunks_qdrant_and_search_hits(
    monkeypatch,
):
    state = {
        "queries": [],
        "chunk_rows": {},
        "qdrant_points": [],
    }

    monkeypatch.setattr(documentary, "get_connection", lambda: FakeConnection(state))
    monkeypatch.setattr(documentary, "get_embedding_client", lambda: FakeEmbeddingClient())
    monkeypatch.setattr(documentary, "get_reranker_client", lambda: FakeReranker())
    monkeypatch.setattr(documentary, "get_ai_backend_preset_name", lambda: "test")
    monkeypatch.setattr(documentary, "get_qdrant_client", lambda: object())
    monkeypatch.setattr(documentary, "ensure_collection", lambda *args, **kwargs: None)
    monkeypatch.setattr(documentary, "uuid4", lambda: CHUNK_ID)

    def fake_upsert_chunks(client, *, collection_name, points):
        state["qdrant_points"].extend(points)

    def fake_search_chunks(
        client,
        *,
        collection_name,
        query_vector,
        limit,
        query_filter=None,
    ):
        state["query_filter"] = query_filter
        return [
            SimpleNamespace(
                score=0.8,
                payload={"chunk_id": str(CHUNK_ID)},
            )
        ]

    monkeypatch.setattr(documentary, "upsert_chunks", fake_upsert_chunks)
    monkeypatch.setattr(documentary, "search_chunks", fake_search_chunks)

    asyncio.run(
        documentary.index_document(
            documentary.IndexRequest(
                document_id=DOCUMENT_ID,
                index_version_id=INDEX_VERSION_ID,
            )
        )
    )
    search_response = asyncio.run(
        documentary.search_documents(
            documentary.SearchRequest(
                query="metadata enrichies",
                index_version_id=INDEX_VERSION_ID,
                top_k=5,
                rerank_top_k=5,
            )
        )
    )

    chunk_metadata = state["chunk_rows"][str(CHUNK_ID)]["metadata"]
    qdrant_payload = state["qdrant_points"][0][2]
    hit_metadata = search_response.hits[0].metadata

    for metadata in (chunk_metadata, qdrant_payload, hit_metadata):
        assert metadata["source_code"] == "metadata_source"
        assert metadata["data_tags"] == ["interne", "juridique"]
        assert metadata["visibility_scope"] == "organization"
        assert metadata["organization_id"] == "org-test"
        assert metadata["access_level"] == "restricted"
        assert metadata["source_url"] == "https://example.test/document"
        assert metadata["publication_date"] == "2026-06-01"
        assert metadata["freshness_status"] == "current"
        assert metadata["language"] == "fr"
        assert metadata["is_primary_source"] is True
        assert metadata["citation_policy"] == "citable"
        assert metadata["rights_status"] == "internal"
        assert metadata["page_start"] == 2
        assert metadata["page_end"] == 2
        assert metadata["content_hash"]

    for metadata in (chunk_metadata, hit_metadata):
        assert metadata["chunking_strategy"] == "generic_window_v1"

    assert "chunking_strategy" not in qdrant_payload
    assert "chunk_index" not in qdrant_payload
    assert "token_count" not in qdrant_payload

    assert qdrant_payload["chunk_id"] == str(CHUNK_ID)
    assert search_response.hits[0].chunk_id == CHUNK_ID


def test_indexing_traces_enabled_noop_chunk_enricher(monkeypatch):
    state = {
        "queries": [],
        "chunk_rows": {},
        "qdrant_points": [],
    }

    class DocumentaryConfig:
        enrichers = [
            EnricherConfig(
                name="noop_enricher_v1",
                enabled=True,
                stages=[EnrichmentStage.post_chunking],
            )
        ]

    class ProjectConfig:
        documentary = DocumentaryConfig()

    monkeypatch.setattr(documentary, "get_project_config", lambda: ProjectConfig())
    monkeypatch.setattr(documentary, "get_connection", lambda: FakeConnection(state))
    monkeypatch.setattr(documentary, "get_embedding_client", lambda: FakeEmbeddingClient())
    monkeypatch.setattr(documentary, "get_ai_backend_preset_name", lambda: "test")
    monkeypatch.setattr(documentary, "get_qdrant_client", lambda: object())
    monkeypatch.setattr(documentary, "ensure_collection", lambda *args, **kwargs: None)
    monkeypatch.setattr(documentary, "uuid4", lambda: CHUNK_ID)
    monkeypatch.setattr(
        documentary,
        "upsert_chunks",
        lambda client, *, collection_name, points: state["qdrant_points"].extend(points),
    )

    asyncio.run(
        documentary.index_document(
            documentary.IndexRequest(
                document_id=DOCUMENT_ID,
                index_version_id=INDEX_VERSION_ID,
            )
        )
    )

    update_run_queries = [
        params
        for query, params in state["queries"]
        if "UPDATE runs" in query and "SET status = 'succeeded'" in query
    ]
    output_payload = json.loads(update_run_queries[-1][0])
    assert output_payload["enrichers"][0]["name"] == "noop_enricher_v1"
    assert output_payload["enrichers"][0]["stage"] == "post_chunking"
    assert output_payload["enrichers"][0]["trace"]["target"] == "chunk"


def test_metadata_filter_restricts_dense_candidates(monkeypatch):
    state = {
        "queries": [],
        "chunk_rows": {},
        "qdrant_points": [],
        "query_filter": None,
    }

    monkeypatch.setattr(documentary, "get_connection", lambda: FakeConnection(state))
    monkeypatch.setattr(documentary, "get_embedding_client", lambda: FakeEmbeddingClient())
    monkeypatch.setattr(documentary, "get_reranker_client", lambda: FakeReranker())
    monkeypatch.setattr(documentary, "get_ai_backend_preset_name", lambda: "test")
    monkeypatch.setattr(documentary, "get_qdrant_client", lambda: object())
    monkeypatch.setattr(documentary, "ensure_collection", lambda *args, **kwargs: None)
    monkeypatch.setattr(documentary, "uuid4", lambda: CHUNK_ID)

    def fake_upsert_chunks(client, *, collection_name, points):
        state["qdrant_points"].extend(points)

    def fake_search_chunks(
        client,
        *,
        collection_name,
        query_vector,
        limit,
        query_filter=None,
    ):
        state["query_filter"] = query_filter
        if query_filter.must[0].match.any == ["other_source"]:
            return []
        return [
            SimpleNamespace(
                score=0.8,
                payload={"chunk_id": str(CHUNK_ID)},
            )
        ]

    monkeypatch.setattr(documentary, "upsert_chunks", fake_upsert_chunks)
    monkeypatch.setattr(documentary, "search_chunks", fake_search_chunks)

    asyncio.run(
        documentary.index_document(
            documentary.IndexRequest(
                document_id=DOCUMENT_ID,
                index_version_id=INDEX_VERSION_ID,
            )
        )
    )
    search_response = asyncio.run(
        documentary.search_documents(
            documentary.SearchRequest(
                query="metadata enrichies",
                index_version_id=INDEX_VERSION_ID,
                top_k=5,
                rerank_top_k=5,
                filters=documentary.SearchMetadataFilters(
                    source_code=["other_source"],
                ),
            )
        )
    )

    assert search_response.hits == []
    assert state["query_filter"].must[0].key == "source_code"
    assert state["query_filter"].must[0].match.any == ["other_source"]


def test_indexing_rejects_unknown_chunk_metadata_before_deleting_chunks(monkeypatch):
    state = {
        "queries": [],
        "chunk_rows": {},
        "qdrant_points": [],
    }
    invalid_chunk = SimpleNamespace(
        chunk_index=0,
        content="Chunk invalide",
        content_sha256="invalid-chunk-hash",
        page_start=None,
        page_end=None,
        token_count=2,
        metadata={"unknown_chunk_field": "value"},
    )

    monkeypatch.setattr(documentary, "get_connection", lambda: FakeConnection(state))
    monkeypatch.setattr(documentary, "get_embedding_client", lambda: FakeEmbeddingClient())
    monkeypatch.setattr(documentary, "chunk_text", lambda *args, **kwargs: [invalid_chunk])

    with pytest.raises(MetadataValidationError, match="unknown_chunk_field"):
        asyncio.run(
            documentary.index_document(
                documentary.IndexRequest(
                    document_id=DOCUMENT_ID,
                    index_version_id=INDEX_VERSION_ID,
                )
            )
        )

    assert not any("DELETE FROM document_chunks" in query for query, _ in state["queries"])


def test_indexing_rejects_document_chunk_propagation_conflict(monkeypatch):
    state = {
        "queries": [],
        "chunk_rows": {},
        "qdrant_points": [],
    }
    conflicting_chunk = SimpleNamespace(
        chunk_index=0,
        content="Chunk conflictuel",
        content_sha256="conflicting-chunk-hash",
        page_start=None,
        page_end=None,
        token_count=2,
        metadata={"source_code": "other_source"},
    )

    monkeypatch.setattr(documentary, "get_connection", lambda: FakeConnection(state))
    monkeypatch.setattr(documentary, "get_embedding_client", lambda: FakeEmbeddingClient())
    monkeypatch.setattr(
        documentary,
        "chunk_text",
        lambda *args, **kwargs: [conflicting_chunk],
    )

    with pytest.raises(MetadataValidationError, match="source_code") as exc_info:
        asyncio.run(
            documentary.index_document(
                documentary.IndexRequest(
                    document_id=DOCUMENT_ID,
                    index_version_id=INDEX_VERSION_ID,
                )
            )
        )

    assert exc_info.value.issues[0].code == "propagation_conflict"
    assert not any("DELETE FROM document_chunks" in query for query, _ in state["queries"])
