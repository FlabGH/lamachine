import importlib.util
import sys
from pathlib import Path

from app.services.documentary.metadata_registry import MetadataRegistry


def _load_audit_module():
    script_path = (
        Path(__file__).resolve().parents[3]
        / "scripts"
        / "qdrant_payload_audit.py"
    )
    spec = importlib.util.spec_from_file_location("qdrant_payload_audit", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _valid_metadata():
    return {
        "document_id": "doc-1",
        "source_code": "ps",
        "chunk_id": "chunk-1",
        "chunk_index": 0,
    }


def _field(**overrides):
    field = {
        "kind": "technical",
        "type": "free",
        "scopes": ["chunk"],
        "required": False,
        "propagate_to_chunks": False,
        "propagate_to_qdrant": False,
        "qdrant_required": False,
        "retrieval_filterable": False,
        "project_input": "forbidden",
        "values_owner": "none",
        "values": None,
        "description": "Test field.",
    }
    field.update(overrides)
    return field


def _registry():
    return MetadataRegistry.model_validate(
        {
            "fields": {
                "document_id": _field(
                    required=True,
                    propagate_to_qdrant=True,
                    qdrant_required=True,
                ),
                "source_code": _field(
                    kind="core_business",
                    required=True,
                    propagate_to_qdrant=True,
                    qdrant_required=True,
                ),
                "chunk_id": _field(
                    required=True,
                    propagate_to_qdrant=True,
                    qdrant_required=True,
                ),
                "chunk_index": _field(type="integer", required=True),
            }
        }
    )


def _valid_payload():
    return {
        "document_id": "doc-1",
        "source_code": "ps",
        "chunk_id": "chunk-1",
    }


def test_audit_payloads_accepts_matching_payload():
    module = _load_audit_module()
    row = module.ChunkPayloadAuditRow(
        chunk_id="chunk-1",
        qdrant_point_id="point-1",
        metadata=_valid_metadata(),
    )
    payload = _valid_payload()

    audit = module.audit_payloads([row], {"point-1": payload}, registry=_registry())

    assert audit["total_chunks"] == 1
    assert audit["total_issues"] == 0
    assert audit["issues"] == []


def test_audit_payloads_reports_missing_point_id():
    module = _load_audit_module()
    row = module.ChunkPayloadAuditRow(
        chunk_id="chunk-1",
        qdrant_point_id=None,
        metadata=_valid_metadata(),
    )

    audit = module.audit_payloads([row], {}, registry=_registry())

    assert audit["issues"][0]["issue"] == "missing_qdrant_point_id"


def test_audit_payloads_reports_invalid_and_mismatched_payload():
    module = _load_audit_module()
    row = module.ChunkPayloadAuditRow(
        chunk_id="chunk-1",
        qdrant_point_id="point-1",
        metadata=_valid_metadata(),
    )
    payload = _valid_payload()
    payload["source_code"] = "rn"
    payload["chunk_index"] = 0

    audit = module.audit_payloads([row], {"point-1": payload}, registry=_registry())
    issues = {issue["issue"] for issue in audit["issues"]}

    assert "invalid_qdrant_payload" in issues
    assert "payload_metadata_mismatch" in issues


def test_audit_payloads_reports_missing_qdrant_required_field():
    module = _load_audit_module()
    row = module.ChunkPayloadAuditRow(
        chunk_id="chunk-1",
        qdrant_point_id="point-1",
        metadata=_valid_metadata(),
    )
    payload = _valid_payload()
    payload.pop("source_code")

    audit = module.audit_payloads([row], {"point-1": payload}, registry=_registry())

    assert audit["issues"][0]["issue"] == "invalid_qdrant_payload"
    assert audit["issues"][1]["issue"] == "payload_metadata_mismatch"
