import importlib.util
import sys
from pathlib import Path


def _load_audit_module():
    script_path = (
        Path(__file__).resolve().parents[3]
        / "scripts"
        / "phase3_qdrant_payload_audit.py"
    )
    spec = importlib.util.spec_from_file_location("phase3_qdrant_payload_audit", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _valid_metadata():
    return {
        "document_id": "doc-1",
        "source_code": "ps",
        "index_version_id": "idx-1",
        "role_documentaire": "doctrine_alliee",
        "theme_tags": ["ia"],
        "visibility_scope": "public",
        "organization_id": "org-1",
        "access_level": "open",
        "data_tags": ["corpus"],
        "service_family": "transverse",
        "service_ids": ["I.1"],
        "page_start": 1,
        "page_end": 2,
    }


def test_audit_payloads_accepts_matching_payload():
    module = _load_audit_module()
    row = module.ChunkPayloadAuditRow(
        chunk_id="chunk-1",
        qdrant_point_id="point-1",
        metadata=_valid_metadata(),
    )
    payload = {"chunk_id": "chunk-1", **_valid_metadata()}

    audit = module.audit_payloads([row], {"point-1": payload})

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

    audit = module.audit_payloads([row], {})

    assert audit["issues"][0]["issue"] == "missing_qdrant_point_id"


def test_audit_payloads_reports_required_key_and_mismatch():
    module = _load_audit_module()
    row = module.ChunkPayloadAuditRow(
        chunk_id="chunk-1",
        qdrant_point_id="point-1",
        metadata=_valid_metadata(),
    )
    payload = {"chunk_id": "chunk-1", **_valid_metadata()}
    payload["source_code"] = "rn"
    payload["theme_tags"] = []

    audit = module.audit_payloads([row], {"point-1": payload})
    issues = {issue["issue"] for issue in audit["issues"]}

    assert "missing_required_payload_keys" in issues
    assert "payload_metadata_mismatch" in issues


def test_audit_payloads_requires_page_range_or_section():
    module = _load_audit_module()
    metadata = _valid_metadata()
    metadata.pop("page_start")
    metadata.pop("page_end")
    row = module.ChunkPayloadAuditRow(
        chunk_id="chunk-1",
        qdrant_point_id="point-1",
        metadata=metadata,
    )
    payload = {"chunk_id": "chunk-1", **metadata}

    audit = module.audit_payloads([row], {"point-1": payload})

    assert audit["issues"][0]["issue"] == "missing_page_range_or_section"
