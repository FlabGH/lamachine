from uuid import UUID

import pytest

from app.services.documentary.metadata_contract import (
    build_chunk_metadata,
    build_qdrant_payload,
    missing_chunk_metadata_keys,
    validate_chunk_metadata,
)


SOURCE_ID = UUID("00000000-0000-0000-0000-000000000001")
DOCUMENT_ID = UUID("00000000-0000-0000-0000-000000000002")
INDEX_VERSION_ID = UUID("00000000-0000-0000-0000-000000000003")


def _metadata(**overrides):
    data = {
        "source_id": SOURCE_ID,
        "document_id": DOCUMENT_ID,
        "document_title": "Document fictif",
        "source_name": "Source fictive",
        "content_sha256": "abc123",
        "index_version_id": INDEX_VERSION_ID,
        "vector_collection": "test_collection",
        "page_start": 1,
        "page_end": 2,
        "extra": {"chunking_strategy": "word_window_v1"},
    }
    data.update(overrides)
    return build_chunk_metadata(**data)


def test_build_chunk_metadata_serializes_ids_and_keeps_pages():
    metadata = _metadata()

    assert metadata["source_id"] == str(SOURCE_ID)
    assert metadata["document_id"] == str(DOCUMENT_ID)
    assert metadata["index_version_id"] == str(INDEX_VERSION_ID)
    assert metadata["document_title"] == "Document fictif"
    assert metadata["source_name"] == "Source fictive"
    assert metadata["page_start"] == 1
    assert metadata["page_end"] == 2
    assert metadata["chunking_strategy"] == "word_window_v1"


def test_build_chunk_metadata_adds_body_section_when_no_page_is_available():
    metadata = _metadata(page_start=None, page_end=None)

    assert metadata["section"] == "body"
    assert "page_start" not in metadata
    assert "page_end" not in metadata
    validate_chunk_metadata(metadata)


def test_build_chunk_metadata_keeps_explicit_section_without_pages():
    metadata = _metadata(page_start=None, page_end=None, section="introduction")

    assert metadata["section"] == "introduction"
    validate_chunk_metadata(metadata)


def test_missing_chunk_metadata_keys_detects_critical_missing_values():
    metadata = _metadata()
    del metadata["source_name"]
    metadata["vector_collection"] = ""

    assert missing_chunk_metadata_keys(metadata) == ["source_name", "vector_collection"]


def test_missing_chunk_metadata_keys_requires_page_or_section():
    metadata = _metadata()
    del metadata["page_start"]
    del metadata["page_end"]

    assert missing_chunk_metadata_keys(metadata) == ["page_or_section"]


def test_validate_chunk_metadata_raises_for_incomplete_metadata():
    metadata = _metadata()
    del metadata["content_sha256"]

    with pytest.raises(ValueError, match="content_sha256"):
        validate_chunk_metadata(metadata)


def test_build_qdrant_payload_contains_chunk_id_and_contract_metadata():
    metadata = _metadata()
    payload = build_qdrant_payload(
        chunk_id=UUID("00000000-0000-0000-0000-000000000004"),
        chunk_metadata=metadata,
    )

    assert payload["chunk_id"] == "00000000-0000-0000-0000-000000000004"
    assert payload["source_id"] == str(SOURCE_ID)
    assert payload["document_title"] == "Document fictif"
    assert payload["source_name"] == "Source fictive"
    assert payload["content_sha256"] == "abc123"
