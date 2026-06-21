from pathlib import Path

import pytest
from pydantic import ValidationError

from app.services.documentary.metadata_registry import (
    MetadataRegistry,
    load_metadata_registry,
)


REGISTRY_PATH = (
    Path(__file__).resolve().parents[1] / "config" / "metadata_registry.yaml"
)


def test_default_registry_loads_canonical_core_fields():
    registry = load_metadata_registry(REGISTRY_PATH)

    assert registry.fields["title"].kind.value == "core_business"
    assert registry.fields["document_type"].kind.value == "project_business"
    assert registry.fields["visibility_scope"].kind.value == "access_control"
    assert registry.fields["chunk_id"].kind.value == "technical"


def test_default_registry_uses_requested_canonical_names_only():
    registry = load_metadata_registry(REGISTRY_PATH)
    excluded = {
        "type_document",
        "statut_metadonnees",
        "mode_qualification",
        "content_sha256",
        "sha256",
        "chunk_size_words",
        "chunk_overlap_words",
        "published_at",
        "document_title",
        "section",
        "origin",
        "source_type",
        "code",
        "name",
        "id",
        "status",
        "metadata",
        "content",
        "text",
        "raw_text",
        "input",
        "output",
        "parameters",
        "response_metadata",
    }

    assert excluded.isdisjoint(registry.fields)
    assert {"document_type", "metadata_status", "qualification_mode"} <= set(
        registry.fields
    )


def test_default_registry_only_declares_explicit_runtime_categories():
    registry = load_metadata_registry(REGISTRY_PATH)

    assert {
        field.kind.value
        for field in registry.fields.values()
    }.isdisjoint({"runtime", "observability"})


def test_registry_rejects_values_for_non_enum_fields():
    with pytest.raises(ValidationError, match="only allowed for enum"):
        MetadataRegistry.model_validate(
            {
                "fields": {
                    "title": {
                        "kind": "core_business",
                        "type": "free",
                        "scopes": ["document"],
                        "required": True,
                        "propagate_to_chunks": False,
                        "propagate_to_qdrant": False,
                        "qdrant_required": False,
                        "retrieval_filterable": False,
                        "values": ["invalid"],
                    }
                }
            }
        )


def test_registry_rejects_enum_without_values():
    with pytest.raises(ValidationError, match="must define non-empty values"):
        MetadataRegistry.model_validate(
            {
                "fields": {
                    "language": {
                        "kind": "core_business",
                        "type": "enum",
                        "scopes": ["document"],
                        "required": False,
                        "propagate_to_chunks": False,
                        "propagate_to_qdrant": False,
                        "qdrant_required": False,
                        "retrieval_filterable": False,
                        "values": None,
                    }
                }
            }
        )


def test_registry_rejects_duplicate_yaml_keys(tmp_path):
    path = tmp_path / "duplicate.yaml"
    path.write_text(
        "\n".join(
            [
                "fields:",
                "  title:",
                "    kind: core_business",
                "    type: free",
                "    scopes: [document]",
                "    required: true",
                "    propagate_to_chunks: false",
                "    propagate_to_qdrant: false",
                "    qdrant_required: false",
                "    retrieval_filterable: false",
                "    values: null",
                "  title:",
                "    kind: core_business",
                "    type: free",
                "    scopes: [document]",
                "    required: false",
                "    propagate_to_chunks: false",
                "    propagate_to_qdrant: false",
                "    qdrant_required: false",
                "    retrieval_filterable: false",
                "    values: null",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Duplicate YAML key: title"):
        load_metadata_registry(path)
