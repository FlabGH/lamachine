import json

from app.services.documentary.metadata_audit import (
    audit_metadata,
    main,
)
from app.services.documentary.metadata_registry import (
    MetadataRegistry,
    MetadataScope,
    ProjectMetadataRegistry,
    merge_metadata_registries,
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
    core = MetadataRegistry.model_validate(
        {
            "fields": {
                "title": _field(required=True),
                "language": _field(
                    type="enum",
                    values_owner="core",
                    values=["fr", "en"],
                ),
                "theme_tags": _field(
                    kind="project_business",
                    type="list",
                    values_owner="project",
                ),
                "chunk_id": _field(
                    type="free",
                    scopes=["chunk"],
                    qdrant_required=True,
                    propagate_to_qdrant=True,
                ),
            }
        }
    )
    project = ProjectMetadataRegistry.model_validate(
        {"overrides": {"theme_tags": {"values": ["budget", "health"]}}}
    )
    return merge_metadata_registries(core, project)


def test_audit_reports_unknown_required_type_and_enum_errors():
    report = audit_metadata(
        {"language": "de", "unknown": "value", "title": 42},
        scope=MetadataScope.document,
        registry=_registry(),
    )

    assert {issue.code for issue in report.issues} == {
        "invalid_enum_value",
        "unknown_field",
        "invalid_type",
    }


def test_audit_reports_missing_required_field():
    report = audit_metadata({}, scope=MetadataScope.document, registry=_registry())

    assert report.issues[0].code == "required_field_missing"
    assert report.issues[0].field == "title"


def test_audit_validates_project_list_values():
    report = audit_metadata(
        {"title": "Test", "theme_tags": ["budget", "invalid"]},
        scope=MetadataScope.document,
        registry=_registry(),
    )

    assert report.issues[0].code == "invalid_list_value"


def test_audit_checks_scope_and_qdrant_requirements():
    document_report = audit_metadata(
        {"title": "Test", "chunk_id": "chunk-1"},
        scope=MetadataScope.document,
        registry=_registry(),
    )
    chunk_report = audit_metadata(
        {},
        scope=MetadataScope.chunk,
        registry=_registry(),
        qdrant_payload=True,
    )

    assert document_report.issues[0].code == "scope_not_allowed"
    assert {issue.code for issue in chunk_report.issues} == {
        "qdrant_required_field_missing"
    }


def test_audit_command_returns_json_and_nonzero_for_issues(tmp_path, capsys):
    core = tmp_path / "core.yaml"
    project = tmp_path / "project.yaml"
    metadata = tmp_path / "metadata.json"
    core.write_text(
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
                "    values_owner: none",
                "    values: null",
                "    description: Test field description.",
            ]
        ),
        encoding="utf-8",
    )
    project.write_text("overrides: {}\nfields: {}\n", encoding="utf-8")
    metadata.write_text(json.dumps({}), encoding="utf-8")

    exit_code = main(
        [
            "--core-registry",
            str(core),
            "--project-registry",
            str(project),
            "--input",
            str(metadata),
            "--scope",
            "document",
        ]
    )

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert output["issues"][0]["code"] == "required_field_missing"
