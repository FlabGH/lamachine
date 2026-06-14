#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID


REPO_ROOT = Path(os.getenv("PHASE3_REPO_ROOT", Path(__file__).resolve().parents[1]))
API_ROOT = Path(os.getenv("PHASE3_API_ROOT", REPO_ROOT / "apps" / "api"))
DEFAULT_REPORT = REPO_ROOT / "artifacts" / "phase3_qdrant_payload_audit.md"
DEFAULT_JSON_REPORT = REPO_ROOT / "artifacts" / "phase3_qdrant_payload_audit.json"

REQUIRED_PAYLOAD_KEYS = {
    "chunk_id",
    "document_id",
    "source_code",
    "index_version_id",
    "role_documentaire",
    "theme_tags",
    "visibility_scope",
    "organization_id",
    "access_level",
    "data_tags",
    "service_family",
    "service_ids",
}


@dataclass(frozen=True)
class ChunkPayloadAuditRow:
    chunk_id: str
    qdrant_point_id: str | None
    metadata: dict[str, Any]


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _normalize_local_service_urls() -> None:
    if Path("/.dockerenv").exists():
        return

    database_url = os.environ.get("DATABASE_URL", "")
    if "@postgres:" in database_url:
        os.environ["DATABASE_URL"] = database_url.replace("@postgres:", "@localhost:")

    qdrant_url = os.environ.get("QDRANT_URL", "")
    if "://qdrant:" in qdrant_url:
        os.environ["QDRANT_URL"] = qdrant_url.replace("://qdrant:", "://localhost:")


def _configure_imports() -> None:
    sys.path.insert(0, str(API_ROOT))


def audit_payloads(
    rows: list[ChunkPayloadAuditRow],
    payloads_by_point_id: dict[str, dict[str, Any] | None],
) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []

    for row in rows:
        if not row.qdrant_point_id:
            issues.append(
                {
                    "chunk_id": row.chunk_id,
                    "issue": "missing_qdrant_point_id",
                }
            )
            continue

        payload = payloads_by_point_id.get(row.qdrant_point_id)
        if payload is None:
            issues.append(
                {
                    "chunk_id": row.chunk_id,
                    "point_id": row.qdrant_point_id,
                    "issue": "missing_qdrant_point",
                }
            )
            continue

        missing_keys = sorted(
            key
            for key in REQUIRED_PAYLOAD_KEYS
            if payload.get(key) in (None, "", [])
        )
        if missing_keys:
            issues.append(
                {
                    "chunk_id": row.chunk_id,
                    "point_id": row.qdrant_point_id,
                    "issue": "missing_required_payload_keys",
                    "keys": missing_keys,
                }
            )

        for key in sorted(REQUIRED_PAYLOAD_KEYS - {"chunk_id"}):
            if payload.get(key) != row.metadata.get(key):
                issues.append(
                    {
                        "chunk_id": row.chunk_id,
                        "point_id": row.qdrant_point_id,
                        "issue": "payload_metadata_mismatch",
                        "key": key,
                        "db_value": row.metadata.get(key),
                        "qdrant_value": payload.get(key),
                    }
                )

        if payload.get("chunk_id") != row.chunk_id:
            issues.append(
                {
                    "chunk_id": row.chunk_id,
                    "point_id": row.qdrant_point_id,
                    "issue": "payload_chunk_id_mismatch",
                    "qdrant_value": payload.get("chunk_id"),
                }
            )

        has_page_range = (
            payload.get("page_start") is not None and payload.get("page_end") is not None
        )
        if not has_page_range and not payload.get("section"):
            issues.append(
                {
                    "chunk_id": row.chunk_id,
                    "point_id": row.qdrant_point_id,
                    "issue": "missing_page_range_or_section",
                }
            )

    return {
        "total_chunks": len(rows),
        "total_issues": len(issues),
        "issues": issues,
    }


def _fetch_index_version(index_version_id: UUID | None) -> dict[str, Any]:
    from app.db import get_connection

    with get_connection() as conn:
        with conn.cursor() as cur:
            if index_version_id is None:
                cur.execute(
                    """
                    SELECT id, name, vector_collection
                    FROM index_versions
                    WHERE is_active = true
                    ORDER BY created_at DESC
                    LIMIT 1
                    """
                )
            else:
                cur.execute(
                    """
                    SELECT id, name, vector_collection
                    FROM index_versions
                    WHERE id = %s
                    """,
                    (index_version_id,),
                )
            row = cur.fetchone()
            if not row:
                raise ValueError("No index version found for Qdrant payload audit")
            return row


def _fetch_chunk_rows(index_version_id: UUID) -> list[ChunkPayloadAuditRow]:
    from app.db import get_connection

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, qdrant_point_id, metadata
                FROM document_chunks
                WHERE index_version_id = %s
                ORDER BY chunk_index, id
                """,
                (index_version_id,),
            )
            return [
                ChunkPayloadAuditRow(
                    chunk_id=str(row["id"]),
                    qdrant_point_id=(
                        str(row["qdrant_point_id"])
                        if row["qdrant_point_id"] is not None
                        else None
                    ),
                    metadata=row["metadata"] or {},
                )
                for row in cur.fetchall()
            ]


def _fetch_qdrant_payloads(
    *,
    collection_name: str,
    point_ids: list[str],
) -> dict[str, dict[str, Any] | None]:
    from app.services.documentary.vector_store import get_qdrant_client

    qdrant = get_qdrant_client()
    payloads_by_id: dict[str, dict[str, Any] | None] = {}
    for start in range(0, len(point_ids), 128):
        batch_ids = point_ids[start : start + 128]
        points = qdrant.retrieve(
            collection_name=collection_name,
            ids=batch_ids,
            with_payload=True,
            with_vectors=False,
        )
        for point in points:
            payloads_by_id[str(point.id)] = point.payload or {}
    for point_id in point_ids:
        payloads_by_id.setdefault(point_id, None)
    return payloads_by_id


def _write_reports(
    *,
    report_path: Path,
    json_report_path: Path,
    index_version: dict[str, Any],
    audit: dict[str, Any],
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    json_report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "index_version_id": str(index_version["id"]),
        "index_version_name": index_version["name"],
        "vector_collection": index_version["vector_collection"],
        **audit,
    }
    json_report_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lines = [
        "# Phase 3 Qdrant Payload Audit",
        "",
        f"Generated at: `{payload['generated_at']}`",
        f"Index version id: `{payload['index_version_id']}`",
        f"Index version name: `{payload['index_version_name']}`",
        f"Vector collection: `{payload['vector_collection']}`",
        "",
        "## Summary",
        "",
        f"- Total chunks: {payload['total_chunks']}",
        f"- Total issues: {payload['total_issues']}",
        "",
        "## Issues",
        "",
    ]
    if not audit["issues"]:
        lines.append("No issue detected.")
    else:
        lines.extend(
            [
                "| chunk_id | point_id | issue | detail |",
                "|---|---|---|---|",
            ]
        )
        for issue in audit["issues"]:
            detail = {
                key: value
                for key, value in issue.items()
                if key not in {"chunk_id", "point_id", "issue"}
            }
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(issue.get("chunk_id", "")),
                        str(issue.get("point_id", "")),
                        str(issue.get("issue", "")),
                        json.dumps(detail, ensure_ascii=False),
                    ]
                )
                + " |"
            )
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit Phase 3 Qdrant payloads.")
    parser.add_argument("--index-version-id", default=None)
    parser.add_argument("--report", default=str(DEFAULT_REPORT.relative_to(REPO_ROOT)))
    parser.add_argument(
        "--json-report",
        default=str(DEFAULT_JSON_REPORT.relative_to(REPO_ROOT)),
    )
    args = parser.parse_args()

    _load_dotenv(REPO_ROOT / ".env")
    _normalize_local_service_urls()
    _configure_imports()

    index_version_id = UUID(args.index_version_id) if args.index_version_id else None
    index_version = _fetch_index_version(index_version_id)
    rows = _fetch_chunk_rows(index_version["id"])
    point_ids = [row.qdrant_point_id for row in rows if row.qdrant_point_id]
    payloads = _fetch_qdrant_payloads(
        collection_name=index_version["vector_collection"],
        point_ids=[str(point_id) for point_id in point_ids],
    )
    audit = audit_payloads(rows, payloads)

    report_path = Path(args.report)
    if not report_path.is_absolute():
        report_path = REPO_ROOT / report_path
    json_report_path = Path(args.json_report)
    if not json_report_path.is_absolute():
        json_report_path = REPO_ROOT / json_report_path

    _write_reports(
        report_path=report_path,
        json_report_path=json_report_path,
        index_version=index_version,
        audit=audit,
    )
    print(report_path)
    print(json_report_path)


if __name__ == "__main__":
    main()
