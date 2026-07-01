from datetime import UTC, date, datetime
from uuid import UUID

import pytest

from app.services.documentary.metadata_contract import (
    build_canonical_chunk_metadata,
    build_chunk_metadata,
    build_qdrant_payload,
    missing_chunk_metadata_keys,
    normalize_document_metadata,
    normalize_ingestion_metadata,
    validate_chunk_metadata,
)


SOURCE_ID = UUID("00000000-0000-0000-0000-000000000001")
DOCUMENT_ID = UUID("00000000-0000-0000-0000-000000000002")
CHUNK_ID = UUID("00000000-0000-0000-0000-000000000004")
INDEX_VERSION_ID = UUID("00000000-0000-0000-0000-000000000003")


def _chunk_metadata(**overrides):
    data = {
        "source_id": SOURCE_ID,
        "document_id": DOCUMENT_ID,
        "chunk_id": CHUNK_ID,
        "title": "Sample document",
        "source_code": "sample",
        "content_hash": "abc123",
        "index_version": INDEX_VERSION_ID,
        "vector_collection": "test_collection",
        "chunk_index": 0,
        "token_count": 10,
        "chunking_version": "generic_window_v1",
        "chunking_strategy": "generic_window_v1",
        "chunk_size": 450,
        "chunk_overlap": 80,
        "page_start": 1,
        "page_end": 2,
    }
    data.update(overrides)
    return build_chunk_metadata(**data)


def test_build_chunk_metadata_serializes_ids_and_keeps_canonical_fields():
    metadata = _chunk_metadata()

    assert metadata["source_id"] == str(SOURCE_ID)
    assert metadata["document_id"] == str(DOCUMENT_ID)
    assert metadata["parent_document_id"] == str(DOCUMENT_ID)
    assert metadata["chunk_id"] == str(CHUNK_ID)
    assert metadata["index_version"] == str(INDEX_VERSION_ID)
    assert metadata["title"] == "Sample document"
    assert metadata["source_code"] == "sample"
    assert metadata["content_hash"] == "abc123"
    assert metadata["page_start"] == 1
    assert metadata["page_end"] == 2
    assert metadata["chunking_strategy"] == "generic_window_v1"
    assert metadata["chunking_version"] == "generic_window_v1"


def test_build_canonical_chunk_metadata_keeps_section_title_when_provided():
    metadata = build_canonical_chunk_metadata(
        source_id=SOURCE_ID,
        document_id=DOCUMENT_ID,
        chunk_id=CHUNK_ID,
        title="Sample document",
        source_code="sample",
        content_hash="abc123",
        index_version=INDEX_VERSION_ID,
        vector_collection="test_collection",
        chunk_index=0,
        token_count=10,
        chunking_version="generic_window_v1",
        chunking_strategy="generic_window_v1",
        chunk_size=450,
        chunk_overlap=80,
        section_title="Introduction",
    )

    assert metadata["section_title"] == "Introduction"
    assert "content_sha256" not in metadata
    assert "index_version_id" not in metadata


def test_missing_chunk_metadata_keys_detects_critical_missing_values():
    metadata = _chunk_metadata()
    del metadata["source_code"]
    metadata["vector_collection"] = ""

    assert missing_chunk_metadata_keys(metadata) == ["source_code", "vector_collection"]


def test_validate_chunk_metadata_raises_for_incomplete_metadata():
    metadata = _chunk_metadata()
    del metadata["content_hash"]

    with pytest.raises(ValueError, match="content_hash"):
        validate_chunk_metadata(metadata)


def test_build_qdrant_payload_contains_chunk_id_and_contract_metadata():
    metadata = _chunk_metadata()
    payload = build_qdrant_payload(
        chunk_id=CHUNK_ID,
        chunk_metadata=metadata,
    )

    assert payload["chunk_id"] == str(CHUNK_ID)
    assert payload["source_id"] == str(SOURCE_ID)
    assert payload["title"] == "Sample document"
    assert payload["source_code"] == "sample"
    assert payload["content_hash"] == "abc123"
    assert payload["chunking_version"] == "generic_window_v1"


def test_normalize_document_metadata_keeps_core_inputs():
    metadata = normalize_document_metadata(
        {
            "title": "Sample document",
            "source_code": " SAMPLE ",
            "theme_tags": [" metadata ", "retrieval", ""],
        }
    )

    assert metadata["title"] == "Sample document"
    assert metadata["source_code"] == "sample"
    assert metadata["theme_tags"] == ["metadata", "retrieval"]
    assert metadata["is_primary_source"] is False
    assert metadata["collected_at"]


def test_normalize_document_metadata_rejects_missing_source_code():
    with pytest.raises(ValueError, match="source_code"):
        normalize_document_metadata({"title": "Sample document"})


def test_normalize_ingestion_metadata_applies_defaults():
    metadata = normalize_ingestion_metadata({}, title="Document test", source_code=" SRC ")

    assert metadata["title"] == "Document test"
    assert metadata["source_code"] == "src"
    assert metadata["data_tags"] == []
    assert metadata["theme_tags"] == []
    assert metadata["is_primary_source"] is False
    assert metadata["collected_at"]


def test_normalize_ingestion_metadata_accepts_project_values():
    metadata = normalize_ingestion_metadata(
        {
            "data_tags": ["dataset"],
            "theme_tags": ["documentation"],
            "visibility_scope": "public",
            "organization_id": "example-org",
            "access_level": "open",
            "source_url": "https://example.test/doc.txt",
            "publication_date": "2026-06-01",
            "collected_at": "2026-06-02T10:00:00Z",
            "language": "en",
            "geographic_scope": "global",
            "temporal_scope": "2026",
            "is_primary_source": True,
            "citation_policy": "citable",
            "rights_status": "open",
        },
        title="Doc",
        source_code="SRC",
    )

    assert metadata["data_tags"] == ["dataset"]
    assert metadata["theme_tags"] == ["documentation"]
    assert metadata["visibility_scope"] == "public"
    assert metadata["organization_id"] == "example-org"
    assert metadata["source_url"] == "https://example.test/doc.txt"
    assert metadata["publication_date"] == "2026-06-01"
    assert metadata["collected_at"] == "2026-06-02T10:00:00+00:00"
    assert metadata["is_primary_source"] is True
    assert metadata["source_code"] == "src"


def test_normalize_ingestion_metadata_accepts_python_date_values():
    metadata = normalize_ingestion_metadata(
        {
            "publication_date": date(2026, 6, 1),
            "collected_at": datetime(2026, 6, 2, 10, 30, tzinfo=UTC),
        }
    )

    assert metadata["publication_date"] == "2026-06-01"
    assert metadata["collected_at"] == "2026-06-02T10:30:00+00:00"


def test_normalize_ingestion_metadata_rejects_invalid_iso_date():
    with pytest.raises(ValueError, match="publication_date"):
        normalize_ingestion_metadata({"publication_date": "juin 2026"})
