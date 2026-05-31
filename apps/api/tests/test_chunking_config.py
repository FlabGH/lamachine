import asyncio
from uuid import UUID

import pytest

from app.api import documentary
from app.api.documentary import ChunkingPreviewRequest
from app.services.documentary.chunking import ChunkingConfig, chunk_text


def _words(count: int) -> str:
    return " ".join(f"mot{i}" for i in range(count))


def test_chunking_config_accepts_valid_values():
    config = ChunkingConfig(
        chunk_size=100,
        chunk_overlap=20,
        split_strategy="word_window",
        min_chunk_size=30,
        max_chunk_size=150,
        chunking_version="word_window_v2",
    )

    assert config.metadata() == {
        "chunking_version": "word_window_v2",
        "split_strategy": "word_window",
        "chunk_size": 100,
        "chunk_overlap": 20,
        "min_chunk_size": 30,
        "max_chunk_size": 150,
    }


def test_chunking_config_rejects_invalid_overlap():
    with pytest.raises(ValueError, match="chunk_overlap"):
        ChunkingConfig(chunk_size=100, chunk_overlap=100)


def test_chunking_config_rejects_invalid_min_and_max():
    with pytest.raises(ValueError, match="min_chunk_size"):
        ChunkingConfig(chunk_size=100, chunk_overlap=10, min_chunk_size=120)

    with pytest.raises(ValueError, match="max_chunk_size"):
        ChunkingConfig(chunk_size=100, chunk_overlap=10, max_chunk_size=90)


def test_different_chunking_configs_produce_different_chunks():
    text = _words(140)

    large_chunks = chunk_text(
        text,
        config=ChunkingConfig(chunk_size=100, chunk_overlap=10, min_chunk_size=20),
    )
    small_chunks = chunk_text(
        text,
        config=ChunkingConfig(chunk_size=50, chunk_overlap=10, min_chunk_size=20),
    )

    assert len(large_chunks) != len(small_chunks)
    assert large_chunks[0].metadata["chunking_version"] == "word_window_v1"
    assert small_chunks[0].metadata["split_strategy"] == "word_window"


def test_chunking_preserves_page_range_and_section_title():
    chunks = chunk_text(
        "[PAGE 2] [SECTION Contexte] " + _words(20),
        config=ChunkingConfig(chunk_size=50, chunk_overlap=5, min_chunk_size=10),
    )

    assert len(chunks) == 1
    assert chunks[0].page_start == 2
    assert chunks[0].page_end == 2
    assert chunks[0].metadata["section_title"] == "Contexte"


def test_chunking_absorbs_small_tail_when_max_size_allows_it():
    text = _words(95)
    chunks = chunk_text(
        text,
        config=ChunkingConfig(
            chunk_size=80,
            chunk_overlap=10,
            min_chunk_size=20,
            max_chunk_size=100,
        ),
    )

    assert len(chunks) == 1
    assert chunks[0].token_count == 95


def test_chunking_preview_returns_chunks_without_persisting(monkeypatch):
    document_id = UUID("00000000-0000-0000-0000-000000000001")
    index_version_id = UUID("00000000-0000-0000-0000-000000000002")
    executed_queries = []

    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, query, params):
            executed_queries.append(query)
            self.params = params

        def fetchone(self):
            if self.params == (document_id,):
                return {
                    "id": document_id,
                    "title": "Document test",
                    "raw_text": "[PAGE 1] " + _words(35),
                }
            if self.params == (index_version_id,):
                return {
                    "id": index_version_id,
                    "chunk_size": 20,
                    "chunk_overlap": 5,
                    "chunking_strategy": "word_window_v1",
                    "chunking_version": "word_window_v1",
                    "split_strategy": "word_window",
                    "min_chunk_size": 10,
                    "max_chunk_size": 40,
                }
            return None

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def cursor(self):
            return FakeCursor()

    monkeypatch.setattr(documentary, "get_connection", lambda: FakeConnection())

    response = asyncio.run(
        documentary.preview_document_chunking(
            document_id,
            ChunkingPreviewRequest(index_version_id=index_version_id),
        )
    )

    assert response.document_id == document_id
    assert response.chunking_config["chunk_size"] == 20
    assert response.chunks
    assert response.chunks[0].content_hash
    assert not any("INSERT" in query.upper() for query in executed_queries)
