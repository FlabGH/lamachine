import pytest

from app.services.documentary.metadata_registry import (
    MetadataRegistry,
    MetadataScope,
)
from app.services.documentary.metadata_validation import (
    MetadataValidationError,
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
        "values_owner": "none",
        "values": None,
        "description": "Test field description.",
    }
    field.update(overrides)
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
