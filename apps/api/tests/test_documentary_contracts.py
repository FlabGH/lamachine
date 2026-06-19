from uuid import UUID

import pytest
from pydantic import ValidationError

from app.services.documentary.contracts import (
    ChunkPayload,
    ChunkRecord,
    DocumentInput,
    DocumentRecord,
    MetadataFilters,
    RetrievalHit,
    RetrievalQuery,
    RetrievalScores,
    SourceReference,
    SourceSpan,
)


SOURCE_ID = UUID("00000000-0000-0000-0000-000000000001")
DOCUMENT_ID = UUID("00000000-0000-0000-0000-000000000002")
INDEX_VERSION_ID = UUID("00000000-0000-0000-0000-000000000003")
CHUNK_ID = UUID("00000000-0000-0000-0000-000000000004")


def _source() -> SourceReference:
    return SourceReference(source_id=SOURCE_ID, source_code=" Source_Test ")


def _span() -> SourceSpan:
    return SourceSpan(page_start=2, page_end=3, section_title=" Contexte ")


def _payload() -> ChunkPayload:
    return ChunkPayload(
        content="Contenu du chunk",
        content_sha256="abc123",
        token_count=4,
        source_span=_span(),
        metadata={"language": "fr", "page_count": 2},
    )


def test_source_reference_normalizes_source_code():
    source = _source()

    assert source.source_id == SOURCE_ID
    assert source.source_code == "source_test"


def test_source_span_validates_page_range_and_normalizes_section_title():
    span = _span()

    assert span.page_start == 2
    assert span.page_end == 3
    assert span.section_title == "Contexte"

    with pytest.raises(ValidationError, match="page_end"):
        SourceSpan(page_start=3, page_end=2)

    with pytest.raises(ValidationError, match="provided together"):
        SourceSpan(page_start=1)


def test_document_contracts_hold_source_content_and_json_metadata():
    document_input = DocumentInput(
        source=_source(),
        title=" Document test ",
        mime_type=" text/plain ",
        filename=" document.txt ",
        raw_text="Texte brut",
        metadata={"tags": ["test"], "published": False},
    )
    document_record = DocumentRecord(
        document_id=DOCUMENT_ID,
        source=document_input.source,
        title=document_input.title,
        mime_type=document_input.mime_type,
        filename=document_input.filename,
        status=" indexed ",
        content_sha256=" document-sha ",
        raw_text=document_input.raw_text,
        metadata=document_input.metadata,
    )

    assert document_input.title == "Document test"
    assert document_input.mime_type == "text/plain"
    assert document_record.status == "indexed"
    assert document_record.metadata == {"tags": ["test"], "published": False}


def test_chunk_contracts_hold_payload_and_persistence_identifiers():
    record = ChunkRecord(
        chunk_id=CHUNK_ID,
        document_id=DOCUMENT_ID,
        index_version_id=INDEX_VERSION_ID,
        chunk_index=0,
        payload=_payload(),
    )

    assert record.payload.source_span.page_start == 2
    assert record.payload.metadata["language"] == "fr"

    with pytest.raises(ValidationError, match="chunk_index"):
        ChunkRecord(
            chunk_id=CHUNK_ID,
            document_id=DOCUMENT_ID,
            index_version_id=INDEX_VERSION_ID,
            chunk_index=-1,
            payload=_payload(),
        )


def test_metadata_filters_trim_and_deduplicate_values():
    filters = MetadataFilters(
        values={
            " source_code ": [" ps ", "ps", "cnil"],
            "language": [" fr "],
        }
    )

    assert filters.values == {
        "source_code": ["ps", "cnil"],
        "language": ["fr"],
    }

    with pytest.raises(ValidationError, match="at least one value"):
        MetadataFilters(values={"source_code": []})


def test_retrieval_contracts_normalize_query_and_keep_scores_as_provided():
    query = RetrievalQuery(
        query="  politique documentaire  ",
        index_version_id=INDEX_VERSION_ID,
        top_k=30,
        rerank_top_k=20,
        filters=MetadataFilters(values={"source_code": ["cnil"]}),
    )
    scores = RetrievalScores(
        dense_score=0.8,
        lexical_score=0.4,
        rerank_score=1.2,
    )
    hit = RetrievalHit(
        chunk_id=CHUNK_ID,
        document_id=DOCUMENT_ID,
        source=_source(),
        source_span=_span(),
        rank_initial=2,
        rank_final=1,
        content=" Extrait retenu ",
        metadata={"source_code": "source_test"},
        scores=scores,
    )

    assert query.query == "politique documentaire"
    assert hit.content == "Extrait retenu"
    assert hit.scores == scores


def test_retrieval_query_rejects_blank_query_and_invalid_limits():
    with pytest.raises(ValidationError, match="query must not be empty"):
        RetrievalQuery(
            query="  ",
            index_version_id=INDEX_VERSION_ID,
            top_k=1,
            rerank_top_k=1,
        )

    with pytest.raises(ValidationError, match="greater than or equal to 1"):
        RetrievalQuery(
            query="test",
            index_version_id=INDEX_VERSION_ID,
            top_k=0,
            rerank_top_k=1,
        )
