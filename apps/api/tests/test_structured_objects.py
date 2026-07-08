import asyncio
from uuid import UUID

from fastapi import HTTPException

from app.api import consultation, documentary
from app.services.ai.clients import EmbeddingResult
from app.services.documentary.contracts import (
    SourceSpan,
    StructuredObjectInput,
    StructuredObjectPayload,
    StructuredObjectProducer,
    StructuredObjectRecord,
)
from app.services.documentary import structured_objects


DOCUMENT_ID = UUID("00000000-0000-0000-0000-000000000001")
CHUNK_ID = UUID("00000000-0000-0000-0000-000000000002")
OBJECT_ID = UUID("00000000-0000-0000-0000-000000000003")


def _input() -> StructuredObjectInput:
    return StructuredObjectInput(
        document_id=DOCUMENT_ID,
        payload=StructuredObjectPayload(
            object_type="recommendation",
            title="Action",
            content="Renforcer le contrôle documentaire.",
            source_span=SourceSpan(page_start=1, page_end=1),
            metadata={"theme": "control"},
            confidence=0.9,
        ),
        producer=StructuredObjectProducer(
            name="fixture_enricher",
            version="v1",
        ),
        source_chunk_ids=[CHUNK_ID],
    )


def _record() -> StructuredObjectRecord:
    return StructuredObjectRecord(
        object_id=OBJECT_ID,
        document_id=DOCUMENT_ID,
        payload=_input().payload,
        producer=_input().producer,
        source_chunk_ids=[CHUNK_ID],
    )


class FakeCursor:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.executed = []
        self._result = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=()):
        self.executed.append((sql, params))
        if "RETURNING" in sql:
            self._result = {
                "id": OBJECT_ID,
                "document_id": DOCUMENT_ID,
                "object_type": "recommendation",
                "title": "Action",
                "content": "Renforcer le contrôle documentaire.",
                "source_span": {"page_start": 1, "page_end": 1},
                "metadata": {"theme": "control"},
                "producer": {"name": "fixture_enricher", "version": "v1"},
                "confidence": 0.9,
                "qdrant_point_id": None,
            }

    def fetchone(self):
        return self._result if self._result is not None else (self.rows[0] if self.rows else None)

    def fetchall(self):
        return self.rows


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def cursor(self):
        return self._cursor


def test_create_structured_object_persists_object_and_source_links(monkeypatch):
    cursor = FakeCursor()
    monkeypatch.setattr(
        structured_objects,
        "get_connection",
        lambda: FakeConnection(cursor),
    )

    record = structured_objects.create_structured_object(_input())

    assert record.object_id == OBJECT_ID
    assert record.payload.object_type == "recommendation"
    assert record.source_chunk_ids == [CHUNK_ID]
    assert len(cursor.executed) == 2
    assert "INSERT INTO structured_objects" in cursor.executed[0][0]
    assert "INSERT INTO structured_object_chunks" in cursor.executed[1][0]


def test_list_structured_objects_returns_records(monkeypatch):
    row = {
        "id": OBJECT_ID,
        "document_id": DOCUMENT_ID,
        "object_type": "recommendation",
        "title": "Action",
        "content": "Renforcer le contrôle documentaire.",
        "source_span": {"page_start": 1, "page_end": 1},
        "metadata": {"theme": "control"},
        "producer": {"name": "fixture_enricher", "version": "v1"},
        "confidence": 0.9,
        "qdrant_point_id": None,
        "source_chunk_ids": [CHUNK_ID],
        "total_count": 1,
    }
    cursor = FakeCursor(rows=[row])
    monkeypatch.setattr(
        structured_objects,
        "get_connection",
        lambda: FakeConnection(cursor),
    )

    total, records = structured_objects.list_structured_objects(
        document_id=DOCUMENT_ID,
        object_type=" Recommendation ",
        limit=10,
        offset=0,
    )

    assert total == 1
    assert records[0].object_id == OBJECT_ID
    assert records[0].payload.object_type == "recommendation"
    assert cursor.executed[0][1][-4:] == (DOCUMENT_ID, "recommendation", 10, 0)


def test_structured_object_api_reads_service_records(monkeypatch):
    monkeypatch.setattr(
        consultation,
        "fetch_structured_objects",
        lambda **kwargs: (1, [_record()]),
    )

    response = consultation.list_structured_objects(
        limit=50,
        offset=0,
        document_id=DOCUMENT_ID,
        object_type="recommendation",
    )

    assert response.total == 1
    assert response.items[0].object_id == OBJECT_ID
    assert response.items[0].source_span == {"page_start": 1, "page_end": 1}


def test_structured_object_api_returns_404_for_missing_object(monkeypatch):
    monkeypatch.setattr(consultation, "fetch_structured_object", lambda object_id: None)

    try:
        consultation.get_structured_object(OBJECT_ID)
    except HTTPException as exc:
        assert exc.status_code == 404
    else:
        raise AssertionError("missing structured object should return 404")


def test_structured_object_qdrant_payload_and_collection_name():
    payload = structured_objects.build_structured_object_qdrant_payload(_record())

    assert structured_objects.structured_object_collection_name("chunks_v1") == (
        "chunks_v1_objects"
    )
    assert payload["object_id"] == str(OBJECT_ID)
    assert payload["document_id"] == str(DOCUMENT_ID)
    assert payload["object_type"] == "recommendation"
    assert payload["source_chunk_ids"] == [str(CHUNK_ID)]
    assert payload["producer"]["name"] == "fixture_enricher"


class FakeEmbeddingClient:
    provider = "fake"
    model = "fake-embedding"
    dimension = 2

    async def embed_texts(self, texts, *, metadata=None):
        return EmbeddingResult(
            vectors=[[0.1, 0.2]],
            provider=self.provider,
            model=self.model,
            dimension=self.dimension,
        )


class FakePoint:
    def __init__(self, object_id, score):
        self.payload = {"object_id": str(object_id)}
        self.score = score


def test_structured_object_search_uses_separate_object_collection(monkeypatch):
    cursor = FakeCursor(rows=[])
    cursor._result = {
        "embedding_provider": "fake",
        "embedding_model": "fake-embedding",
        "embedding_dimension": 2,
        "vector_collection": "chunks_v1",
    }
    monkeypatch.setattr(
        consultation,
        "get_connection",
        lambda: FakeConnection(cursor),
    )
    embedding_calls = []

    def fake_embedding_client_factory(provider=None, model=None):
        embedding_calls.append((provider, model))
        return FakeEmbeddingClient()

    monkeypatch.setattr(documentary, "get_embedding_client", fake_embedding_client_factory)
    monkeypatch.setattr(consultation, "get_qdrant_client", lambda: object())

    captured = {}

    def fake_search_points(*args, **kwargs):
        captured.update(kwargs)
        return [FakePoint(OBJECT_ID, 0.91)]

    monkeypatch.setattr(consultation, "search_points", fake_search_points)
    monkeypatch.setattr(
        consultation,
        "get_structured_objects_by_ids",
        lambda object_ids: {OBJECT_ID: _record()},
    )

    response = asyncio.run(
        consultation.search_structured_objects(
            consultation.StructuredObjectSearchRequest(
                query="gouvernance documentaire",
                index_version_id=UUID("00000000-0000-0000-0000-000000000006"),
                top_k=5,
                object_type=" Recommendation ",
            )
        )
    )

    assert response.vector_collection == "chunks_v1_objects"
    assert response.hits[0].object_id == OBJECT_ID
    assert response.hits[0].rank == 1
    assert response.hits[0].score == 0.91
    assert captured["collection_name"] == "chunks_v1_objects"
    assert captured["limit"] == 5
    assert captured["query_filter"].must[0].key == "object_type"
    assert embedding_calls == [("fake", "fake-embedding")]
