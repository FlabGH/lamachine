from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.services.documentary.metadata_registry import (
    MetadataRegistry,
    MetadataScope,
    load_metadata_registry,
)
from app.services.documentary.metadata_validation import (
    MetadataValidationError,
    validate_metadata,
)


class MetadataAuditIssue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str
    field: str | None = None
    message: str


class MetadataAuditReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    scope: MetadataScope
    qdrant_payload: bool
    issues: list[MetadataAuditIssue] = Field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.issues

    def output(self) -> dict[str, Any]:
        return {
            "scope": self.scope.value,
            "qdrant_payload": self.qdrant_payload,
            "valid": self.valid,
            "issues": [issue.model_dump() for issue in self.issues],
        }


def audit_metadata(
    metadata: dict[str, Any],
    *,
    scope: MetadataScope,
    registry: MetadataRegistry,
    qdrant_payload: bool = False,
) -> MetadataAuditReport:
    issues: list[MetadataAuditIssue] = []
    try:
        validate_metadata(metadata, scope=scope, registry=registry)
    except MetadataValidationError as exc:
        issues.extend(
            MetadataAuditIssue(
                code=issue.code,
                field=issue.field,
                message=issue.message,
            )
            for issue in exc.issues
        )
    if qdrant_payload and scope is MetadataScope.chunk:
        for name, field in registry.fields.items():
            if field.qdrant_required and name not in metadata:
                issues.append(
                    MetadataAuditIssue(
                        code="qdrant_required_field_missing",
                        field=name,
                        message="Qdrant-required field is missing",
                    )
                )

    return MetadataAuditReport(
        scope=scope,
        qdrant_payload=qdrant_payload,
        issues=issues,
    )


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit metadata against registries")
    parser.add_argument("--core-registry", required=True, type=Path)
    parser.add_argument("--project-registry", required=True, type=Path)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--scope", required=True, choices=[scope.value for scope in MetadataScope])
    parser.add_argument("--qdrant-payload", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        registry = load_metadata_registry(args.core_registry, args.project_registry)
        metadata = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(metadata, dict):
            raise ValueError("Input JSON must be an object")
        report = audit_metadata(
            metadata,
            scope=MetadataScope(args.scope),
            registry=registry,
            qdrant_payload=args.qdrant_payload,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}))
        return 1

    print(json.dumps(report.output(), sort_keys=True))
    return 0 if report.valid else 1


if __name__ == "__main__":
    sys.exit(main())
