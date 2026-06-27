import pytest

from app.services.documentary.metadata_registry import (
    MetadataRegistry,
    MetadataScope,
)
from app.services.documentary.metadata_validation import (
    MetadataValidationError,
    build_qdrant_payload,
    propagate_document_metadata,
    validate_qdrant_payload,
    validate_retrieval_filters,
    validate_metadata,
)


def _field(**overrides):
    field = {
        "kind": "core_business",
        "type": "free",
        "scopes": ["document"],
        "required": False,
        "propagate_to_chunks": False,
        "propagate_to_qdrant": False,
        "qdrant_required": False,
        "retrieval_filterable": False,
        "project_input": "optional",
        "values_owner": "none",
        "values": None,
        "description": "Test field description.",
    }
    field.update(overrides)
    if "project_input" not in overrides and "document" not in field["scopes"]:
        field["project_input"] = "forbidden"
    return field


def _registry():
    return MetadataRegistry.model_validate(
        {
            "fields": {
                "title": _field(required=True),
                "language": _field(
                    type="enum",
                    values_owner="core",
                    values=["fr", "en"],
                ),
                "theme_tags": _field(
                    type="list",
                    values_owner="project",
                    values=["budget", "health"],
                ),
                "priority": _field(type="integer"),
                "confidence": _field(type="number"),
                "is_public": _field(type="boolean"),
                "publication_date": _field(type="date"),
                "validated_at": _field(type="datetime"),
                "details": _field(type="object"),
                "chunk_id": _field(scopes=["chunk"], required=True),
                "document_type": _field(type="enum", values_owner="project"),
            }
        }
    )


def _issue_codes(metadata, scope=MetadataScope.document):
    with pytest.raises(MetadataValidationError) as exc_info:
        validate_metadata(metadata, scope=scope, registry=_registry())
    return {issue.code for issue in exc_info.value.issues}


def test_validate_metadata_accepts_valid_document_metadata():
    metadata = {
        "title": "Document",
        "language": "fr",
        "theme_tags": ["budget"],
        "priority": 1,
        "confidence": 0.8,
        "is_public": True,
        "publication_date": "2026-06-21",
        "validated_at": "2026-06-21T10:30:00Z",
        "details": {"origin": "test"},
    }

    assert validate_metadata(
        metadata,
        scope=MetadataScope.document,
        registry=_registry(),
    ) == metadata


@pytest.mark.parametrize(
    "metadata, expected_code",
    [
        ({"title": "Document", "unknown": "x"}, "unknown_field"),
        ({"title": "Document", "chunk_id": "chunk-1"}, "scope_not_allowed"),
        ({}, "required_field_missing"),
        ({"title": " "}, "required_value_empty"),
        ({"title": "Document", "priority": True}, "invalid_type"),
        ({"title": "Document", "language": "de"}, "invalid_enum_value"),
        ({"title": "Document", "theme_tags": ["invalid"]}, "invalid_list_value"),
        ({"title": "Document", "document_type": "report"}, "enum_values_not_configured"),
        ({"title": "Document", "publication_date": "21/06/2026"}, "invalid_type"),
        ({"title": "Document", "validated_at": "tomorrow"}, "invalid_type"),
    ],
)
def test_validate_metadata_rejects_invalid_document_metadata(metadata, expected_code):
    assert expected_code in _issue_codes(metadata)


def test_validate_metadata_rejects_empty_optional_value_when_provided():
    assert "empty_value" in _issue_codes({"title": "Document", "language": ""})


def test_validate_metadata_requires_chunk_fields_in_chunk_scope():
    assert "required_field_missing" in _issue_codes({}, scope=MetadataScope.chunk)


def test_propagate_document_metadata_copies_declared_values():
    registry = MetadataRegistry.model_validate(
        {
            "fields": {
                "theme_tags": _field(
                    type="list",
                    scopes=["document", "chunk"],
                    propagate_to_chunks=True,
                    values_owner="project",
                ),
                "author": _field(),
            }
        }
    )
    document_metadata = {"theme_tags": ["budget"]}

    propagated = propagate_document_metadata(
        document_metadata,
        {"chunk_index": 0},
        registry=registry,
    )

    assert propagated["theme_tags"] == ["budget"]
    assert propagated["theme_tags"] is not document_metadata["theme_tags"]
    assert "author" not in propagated


def test_propagate_document_metadata_rejects_conflicting_chunk_value():
    registry = MetadataRegistry.model_validate(
        {
            "fields": {
                "source_code": _field(
                    scopes=["document", "chunk"],
                    propagate_to_chunks=True,
                )
            }
        }
    )

    with pytest.raises(MetadataValidationError) as exc_info:
        propagate_document_metadata(
            {"source_code": "official"},
            {"source_code": "other"},
            registry=registry,
        )

    assert exc_info.value.issues[0].code == "propagation_conflict"


def test_build_qdrant_payload_filters_and_validates_chunk_metadata():
    registry = MetadataRegistry.model_validate(
        {
            "fields": {
                "source_code": _field(
                    scopes=["chunk"],
                    required=True,
                    propagate_to_qdrant=True,
                    qdrant_required=True,
                ),
                "chunk_id": _field(
                    scopes=["chunk"],
                    required=True,
                    propagate_to_qdrant=True,
                    qdrant_required=True,
                ),
                "chunk_index": _field(
                    type="integer",
                    scopes=["chunk"],
                    required=True,
                ),
            }
        }
    )

    payload = build_qdrant_payload(
        {"source_code": "official", "chunk_id": "chunk-1", "chunk_index": 0},
        registry=registry,
    )

    assert payload == {"source_code": "official", "chunk_id": "chunk-1"}


def test_validate_qdrant_payload_rejects_missing_required_and_disallowed_fields():
    registry = MetadataRegistry.model_validate(
        {
            "fields": {
                "chunk_id": _field(
                    scopes=["chunk"],
                    required=True,
                    propagate_to_qdrant=True,
                    qdrant_required=True,
                ),
                "chunk_index": _field(type="integer", scopes=["chunk"]),
            }
        }
    )

    with pytest.raises(MetadataValidationError) as missing_exc:
        validate_qdrant_payload({}, registry=registry)
    assert missing_exc.value.issues[0].code == "required_field_missing"

    with pytest.raises(MetadataValidationError) as disallowed_exc:
        validate_qdrant_payload(
            {"chunk_id": "chunk-1", "chunk_index": 0},
            registry=registry,
        )
    assert disallowed_exc.value.issues[0].code == "qdrant_field_not_allowed"


def test_validate_qdrant_payload_revalidates_enum_values():
    registry = MetadataRegistry.model_validate(
        {
            "fields": {
                "chunk_id": _field(
                    scopes=["chunk"],
                    required=True,
                    propagate_to_qdrant=True,
                    qdrant_required=True,
                ),
                "language": _field(
                    type="enum",
                    scopes=["chunk"],
                    propagate_to_qdrant=True,
                    values_owner="core",
                    values=["fr", "en"],
                ),
            }
        }
    )

    with pytest.raises(MetadataValidationError) as exc_info:
        validate_qdrant_payload(
            {"chunk_id": "chunk-1", "language": "de"},
            registry=registry,
        )

    assert exc_info.value.issues[0].code == "invalid_enum_value"


def test_validate_retrieval_filters_accepts_and_deduplicates_values():
    registry = MetadataRegistry.model_validate(
        {
            "fields": {
                "language": _field(
                    type="enum",
                    scopes=["chunk"],
                    propagate_to_qdrant=True,
                    retrieval_filterable=True,
                    values_owner="core",
                    values=["fr", "en"],
                ),
                "theme_tags": _field(
                    type="list",
                    scopes=["chunk"],
                    propagate_to_qdrant=True,
                    retrieval_filterable=True,
                    values_owner="project",
                    values=["budget", "health"],
                ),
            }
        }
    )

    assert validate_retrieval_filters(
        {"language": ["fr", "fr"], "theme_tags": ["budget", "budget"]},
        registry=registry,
    ) == {"language": ["fr"], "theme_tags": ["budget"]}


@pytest.mark.parametrize(
    ("filters", "code"),
    [
        ({"unknown": ["value"]}, "unknown_filter_field"),
        ({"title": ["Document"]}, "filter_not_allowed"),
        ({"language": ["de"]}, "invalid_enum_value"),
        ({"theme_tags": ["invalid"]}, "invalid_list_value"),
        ({"language": []}, "invalid_filter_values"),
    ],
)
def test_validate_retrieval_filters_rejects_invalid_values(filters, code):
    registry = MetadataRegistry.model_validate(
        {
            "fields": {
                "title": _field(scopes=["chunk"]),
                "language": _field(
                    type="enum",
                    scopes=["chunk"],
                    propagate_to_qdrant=True,
                    retrieval_filterable=True,
                    values_owner="core",
                    values=["fr", "en"],
                ),
                "theme_tags": _field(
                    type="list",
                    scopes=["chunk"],
                    propagate_to_qdrant=True,
                    retrieval_filterable=True,
                    values_owner="project",
                    values=["budget"],
                ),
            }
        }
    )

    with pytest.raises(MetadataValidationError) as exc_info:
        validate_retrieval_filters(filters, registry=registry)

    assert exc_info.value.issues[0].code == code
