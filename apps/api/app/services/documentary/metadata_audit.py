from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.services.documentary.metadata_registry import (
    MetadataFieldDefinition,
    MetadataRegistry,
    MetadataScope,
    MetadataType,
    load_metadata_registry,
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


def _type_error(field: MetadataFieldDefinition, value: Any) -> str | None:
    if field.type is MetadataType.free:
        return None if isinstance(value, str) else "expected a string"
    if field.type is MetadataType.boolean:
        return None if isinstance(value, bool) else "expected a boolean"
    if field.type is MetadataType.number:
        return (
            None
            if isinstance(value, int | float) and not isinstance(value, bool)
            else "expected a number"
        )
    if field.type is MetadataType.integer:
        return (
            None
            if isinstance(value, int) and not isinstance(value, bool)
            else "expected an integer"
        )
    if field.type is MetadataType.object:
        return None if isinstance(value, dict) else "expected an object"
    if field.type is MetadataType.list:
        return None if isinstance(value, list) else "expected a list"
    if field.type is MetadataType.enum:
        return None if isinstance(value, str) else "expected an enum string"
    if field.type is MetadataType.date:
        if not isinstance(value, str):
            return "expected an ISO date string"
        try:
            date.fromisoformat(value)
        except ValueError:
            return "expected an ISO date string"
        return None
    if field.type is MetadataType.datetime:
        if not isinstance(value, str):
            return "expected an ISO datetime string"
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return "expected an ISO datetime string"
        return None
    return "unsupported metadata type"


def audit_metadata(
    metadata: dict[str, Any],
    *,
    scope: MetadataScope,
    registry: MetadataRegistry,
    qdrant_payload: bool = False,
) -> MetadataAuditReport:
    issues: list[MetadataAuditIssue] = []

    for name, value in metadata.items():
        field = registry.fields.get(name)
        if field is None:
            issues.append(
                MetadataAuditIssue(
                    code="unknown_field",
                    field=name,
                    message="Field is not declared in the effective metadata registry",
                )
            )
            continue
        if scope not in field.scopes:
            issues.append(
                MetadataAuditIssue(
                    code="scope_not_allowed",
                    field=name,
                    message=f"Field is not allowed in {scope.value} scope",
                )
            )
            continue

        type_error = _type_error(field, value)
        if type_error:
            issues.append(
                MetadataAuditIssue(
                    code="invalid_type",
                    field=name,
                    message=type_error,
                )
            )
            continue

        if field.type is MetadataType.enum and field.values and value not in field.values:
            issues.append(
                MetadataAuditIssue(
                    code="invalid_enum_value",
                    field=name,
                    message=f"Value must be one of: {', '.join(field.values)}",
                )
            )
        if field.type is MetadataType.list and field.values:
            invalid_values = [item for item in value if item not in field.values]
            if invalid_values:
                issues.append(
                    MetadataAuditIssue(
                        code="invalid_list_value",
                        field=name,
                        message=(
                            "List contains values outside the registry: "
                            f"{', '.join(map(str, invalid_values))}"
                        ),
                    )
                )

    for name, field in registry.fields.items():
        if scope in field.scopes and field.required and name not in metadata:
            issues.append(
                MetadataAuditIssue(
                    code="required_field_missing",
                    field=name,
                    message="Required field is missing",
                )
            )
        if (
            qdrant_payload
            and scope is MetadataScope.chunk
            and field.qdrant_required
            and name not in metadata
        ):
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
