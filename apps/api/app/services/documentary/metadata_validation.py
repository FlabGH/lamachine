from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from app.services.documentary.metadata_registry import (
    MetadataRegistry,
    MetadataScope,
    MetadataType,
)


@dataclass(frozen=True)
class MetadataValidationIssue:
    code: str
    field: str | None
    message: str


class MetadataValidationError(ValueError):
    def __init__(self, issues: list[MetadataValidationIssue]) -> None:
        self.issues = tuple(issues)
        super().__init__(
            "; ".join(
                f"{issue.field}: {issue.message}" if issue.field else issue.message
                for issue in self.issues
            )
        )


def _is_empty(value: Any) -> bool:
    return value is None or (
        isinstance(value, (str, list, dict)) and not value
    ) or (isinstance(value, str) and not value.strip())


def _type_error(field_type: MetadataType, value: Any) -> str | None:
    if field_type in {MetadataType.free, MetadataType.enum}:
        return None if isinstance(value, str) else "expected a string"
    if field_type is MetadataType.boolean:
        return None if isinstance(value, bool) else "expected a boolean"
    if field_type is MetadataType.number:
        return (
            None
            if isinstance(value, int | float) and not isinstance(value, bool)
            else "expected a number"
        )
    if field_type is MetadataType.integer:
        return (
            None
            if isinstance(value, int) and not isinstance(value, bool)
            else "expected an integer"
        )
    if field_type is MetadataType.object:
        return None if isinstance(value, dict) else "expected an object"
    if field_type is MetadataType.list:
        return None if isinstance(value, list) else "expected a list"
    if field_type is MetadataType.date:
        if not isinstance(value, str):
            return "expected an ISO date string"
        try:
            date.fromisoformat(value)
        except ValueError:
            return "expected an ISO date string"
        return None
    if field_type is MetadataType.datetime:
        if not isinstance(value, str):
            return "expected an ISO datetime string"
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return "expected an ISO datetime string"
        return None
    return "unsupported metadata type"


def validate_metadata(
    metadata: dict[str, Any],
    *,
    scope: MetadataScope,
    registry: MetadataRegistry,
    required_field_names: set[str] | None = None,
) -> dict[str, Any]:
    """Validate documentary metadata against the effective registry."""
    issues: list[MetadataValidationIssue] = []

    for name, value in metadata.items():
        field = registry.fields.get(name)
        if field is None:
            issues.append(
                MetadataValidationIssue(
                    code="unknown_field",
                    field=name,
                    message="Field is not declared in the effective metadata registry",
                )
            )
            continue
        if scope not in field.scopes:
            issues.append(
                MetadataValidationIssue(
                    code="scope_not_allowed",
                    field=name,
                    message=f"Field is not allowed in {scope.value} scope",
                )
            )
            continue

        if _is_empty(value):
            issues.append(
                MetadataValidationIssue(
                    code="required_value_empty" if field.required else "empty_value",
                    field=name,
                    message="Required field must not be empty"
                    if field.required
                    else "Field must not be empty when provided",
                )
            )
            continue

        type_error = _type_error(field.type, value)
        if type_error:
            issues.append(
                MetadataValidationIssue(
                    code="invalid_type",
                    field=name,
                    message=type_error,
                )
            )
            continue

        if field.type is MetadataType.enum:
            if not field.values:
                issues.append(
                    MetadataValidationIssue(
                        code="enum_values_not_configured",
                        field=name,
                        message="Enum field has no effective allowed values",
                    )
                )
            elif value not in field.values:
                issues.append(
                    MetadataValidationIssue(
                        code="invalid_enum_value",
                        field=name,
                        message=f"Value must be one of: {', '.join(field.values)}",
                    )
                )

        if field.type is MetadataType.list and field.values:
            invalid_values = [item for item in value if item not in field.values]
            if invalid_values:
                issues.append(
                    MetadataValidationIssue(
                        code="invalid_list_value",
                        field=name,
                        message=(
                            "List contains values outside the registry: "
                            f"{', '.join(map(str, invalid_values))}"
                        ),
                    )
                )

    required_names = required_field_names
    if required_names is None:
        required_names = {
            name
            for name, field in registry.fields.items()
            if scope in field.scopes and field.required
        }
    for name in required_names:
        if name not in metadata:
            issues.append(
                MetadataValidationIssue(
                    code="required_field_missing",
                    field=name,
                    message="Required field is missing",
                )
            )

    if issues:
        raise MetadataValidationError(issues)
    return dict(metadata)


def validate_qdrant_payload(
    payload: dict[str, Any],
    *,
    registry: MetadataRegistry,
) -> dict[str, Any]:
    issues = [
        MetadataValidationIssue(
            code="qdrant_field_not_allowed",
            field=name,
            message="Field does not propagate to Qdrant",
        )
        for name in payload
        if (field := registry.fields.get(name)) is not None
        and not field.propagate_to_qdrant
    ]
    if issues:
        raise MetadataValidationError(issues)

    required_names = {
        name
        for name, field in registry.fields.items()
        if field.qdrant_required
    }
    return validate_metadata(
        payload,
        scope=MetadataScope.chunk,
        registry=registry,
        required_field_names=required_names,
    )


def build_qdrant_payload(
    chunk_metadata: dict[str, Any],
    *,
    registry: MetadataRegistry,
) -> dict[str, Any]:
    validate_metadata(
        chunk_metadata,
        scope=MetadataScope.chunk,
        registry=registry,
    )
    payload = {
        name: deepcopy(value)
        for name, value in chunk_metadata.items()
        if registry.fields[name].propagate_to_qdrant
    }
    return validate_qdrant_payload(payload, registry=registry)


def propagate_document_metadata(
    document_metadata: dict[str, Any],
    chunk_metadata: dict[str, Any],
    *,
    registry: MetadataRegistry,
) -> dict[str, Any]:
    """Copy declared document metadata into a chunk without silent overrides."""
    propagated = dict(chunk_metadata)
    issues: list[MetadataValidationIssue] = []

    for name, field in registry.fields.items():
        if not field.propagate_to_chunks or name not in document_metadata:
            continue

        document_value = document_metadata[name]
        if name not in propagated:
            propagated[name] = deepcopy(document_value)
            continue
        if propagated[name] != document_value:
            issues.append(
                MetadataValidationIssue(
                    code="propagation_conflict",
                    field=name,
                    message=(
                        "Chunk value conflicts with the propagated document value"
                    ),
                )
            )

    if issues:
        raise MetadataValidationError(issues)
    return propagated
