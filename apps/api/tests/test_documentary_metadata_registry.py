from pathlib import Path

import pytest
from pydantic import ValidationError

from app.services.documentary.metadata_registry import (
    MetadataRegistry,
    ProjectMetadataRegistry,
    load_core_metadata_registry,
    load_metadata_registry,
    load_project_metadata_registry,
    merge_metadata_registries,
)


CONFIG_DIR = Path(__file__).resolve().parents[1] / "config"
CORE_REGISTRY_PATH = CONFIG_DIR / "metadata_registry.core.yaml"
PROJECT_REGISTRY_PATH = CONFIG_DIR / "metadata_registry.project.yaml"


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


def test_core_and_default_project_registries_load():
    core = load_core_metadata_registry(CORE_REGISTRY_PATH)
    project = load_project_metadata_registry(PROJECT_REGISTRY_PATH)
    effective = load_metadata_registry(CORE_REGISTRY_PATH, PROJECT_REGISTRY_PATH)

    assert core.fields["language"].values_owner.value == "core"
    assert core.fields["document_type"].values_owner.value == "project"
    assert all(field.description for field in core.fields.values())
    assert project.overrides == {}
    assert project.fields == {}
    assert effective == core


def test_project_values_are_merged_into_open_core_field():
    core = MetadataRegistry.model_validate(
        {"fields": {"document_type": _field(type="enum", values_owner="project")}}
    )
    project = ProjectMetadataRegistry.model_validate(
        {"overrides": {"document_type": {"values": ["report", "article"]}}}
    )

    effective = merge_metadata_registries(core, project)

    assert effective.fields["document_type"].values == ["report", "article"]


def test_project_can_override_core_description_without_opening_values():
    core = MetadataRegistry.model_validate({"fields": {"title": _field()}})
    project = ProjectMetadataRegistry.model_validate(
        {"overrides": {"title": {"description": "Project title label."}}}
    )

    effective = merge_metadata_registries(core, project)

    assert effective.fields["title"].description == "Project title label."


def test_project_override_requires_values_or_description():
    with pytest.raises(ValidationError, match="values or description"):
        ProjectMetadataRegistry.model_validate({"overrides": {"title": {}}})


def test_registry_rejects_empty_description():
    with pytest.raises(ValidationError, match="description"):
        MetadataRegistry.model_validate(
            {"fields": {"title": _field(description=" ")}}
        )


def test_project_can_add_project_business_field_without_python_code():
    core = MetadataRegistry.model_validate({"fields": {"title": _field()}})
    project = ProjectMetadataRegistry.model_validate(
        {
            "fields": {
                "role_documentaire": _field(
                    kind="project_business",
                    type="enum",
                    values_owner="project",
                    values=["reference", "opponent"],
                    description="Project documentary role.",
                )
            }
        }
    )

    effective = merge_metadata_registries(core, project)

    assert effective.fields["role_documentaire"].kind.value == "project_business"
    assert effective.fields["role_documentaire"].values == ["reference", "opponent"]


def test_list_fields_can_be_open_to_project_values():
    core = load_core_metadata_registry(CORE_REGISTRY_PATH)

    assert core.fields["theme_tags"].type.value == "list"
    assert core.fields["theme_tags"].values_owner.value == "project"
    assert core.fields["theme_tags"].values is None
    assert core.fields["data_tags"].type.value == "list"
    assert core.fields["data_tags"].values is None


def test_project_cannot_override_closed_core_values():
    core = MetadataRegistry.model_validate(
        {
            "fields": {
                "language": _field(
                    type="enum",
                    values_owner="core",
                    values=["fr", "en"],
                )
            }
        }
    )
    project = ProjectMetadataRegistry.model_validate(
        {"overrides": {"language": {"values": ["fr"]}}}
    )

    with pytest.raises(ValueError, match="does not allow project values"):
        merge_metadata_registries(core, project)


def test_registry_rejects_invalid_qdrant_requirement():
    with pytest.raises(ValidationError, match="must propagate_to_qdrant"):
        MetadataRegistry.model_validate(
            {"fields": {"document_id": _field(qdrant_required=True)}}
        )


def test_registry_rejects_propagation_without_document_and_chunk_scopes():
    with pytest.raises(ValidationError, match="document and chunk scopes"):
        MetadataRegistry.model_validate(
            {"fields": {"title": _field(propagate_to_chunks=True)}}
        )


def test_registry_rejects_qdrant_field_without_chunk_scope():
    with pytest.raises(ValidationError, match="chunk scope"):
        MetadataRegistry.model_validate(
            {
                "fields": {
                    "title": _field(
                        scopes=["document"],
                        propagate_to_qdrant=True,
                    )
                }
            }
        )


def test_registry_rejects_values_for_unsupported_type():
    with pytest.raises(ValidationError, match="enum or list"):
        MetadataRegistry.model_validate(
            {"fields": {"title": _field(values_owner="project", values=["x"])}}
        )


def test_registry_rejects_core_values_owner_without_values():
    with pytest.raises(ValidationError, match="requires non-empty values"):
        MetadataRegistry.model_validate(
            {
                "fields": {
                    "language": _field(type="enum", values_owner="core")
                }
            }
        )


def test_project_cannot_add_technical_field():
    core = MetadataRegistry.model_validate({"fields": {"title": _field()}})
    project = ProjectMetadataRegistry.model_validate(
        {
            "fields": {
                "custom_runtime": _field(
                    kind="technical",
                    values_owner="project",
                )
            }
        }
    )

    with pytest.raises(ValueError, match="project_business"):
        merge_metadata_registries(core, project)


def test_registry_rejects_duplicate_yaml_keys(tmp_path):
    path = tmp_path / "duplicate.yaml"
    path.write_text(
        "\n".join(
            [
                "fields:",
                "  title: {}",
                "  title: {}",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Duplicate YAML key: title"):
        load_core_metadata_registry(path)
