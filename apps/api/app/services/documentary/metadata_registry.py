from __future__ import annotations

from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.services.project_config import get_project_config


API_ROOT = Path(__file__).resolve().parents[3]


class MetadataKind(str, Enum):
    core_business = "core_business"
    project_business = "project_business"
    technical = "technical"
    access_control = "access_control"
    runtime = "runtime"
    observability = "observability"


class MetadataType(str, Enum):
    enum = "enum"
    free = "free"
    boolean = "boolean"
    number = "number"
    integer = "integer"
    date = "date"
    datetime = "datetime"
    object = "object"
    list = "list"


class ValuesOwner(str, Enum):
    core = "core"
    project = "project"
    none = "none"


class MetadataScope(str, Enum):
    document = "document"
    chunk = "chunk"
    run = "run"
    model_call = "model_call"
    retrieval_hit = "retrieval_hit"


class MetadataFieldDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: MetadataKind
    type: MetadataType
    scopes: list[MetadataScope] = Field(min_length=1)
    required: bool
    propagate_to_chunks: bool
    propagate_to_qdrant: bool
    qdrant_required: bool
    retrieval_filterable: bool
    values_owner: ValuesOwner
    values: list[str] | None = None
    description: str = Field(min_length=1)

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("description must not be empty")
        return normalized

    @field_validator("scopes")
    @classmethod
    def reject_duplicate_scopes(
        cls,
        scopes: list[MetadataScope],
    ) -> list[MetadataScope]:
        if len(scopes) != len(set(scopes)):
            raise ValueError("scopes must not contain duplicates")
        return scopes

    @model_validator(mode="after")
    def validate_values(self) -> "MetadataFieldDefinition":
        if self.qdrant_required and not self.propagate_to_qdrant:
            raise ValueError(
                "qdrant_required fields must propagate_to_qdrant"
            )
        scopes = set(self.scopes)
        if self.propagate_to_chunks and not {
            MetadataScope.document,
            MetadataScope.chunk,
        }.issubset(scopes):
            raise ValueError(
                "propagate_to_chunks fields must allow document and chunk scopes"
            )
        if self.propagate_to_qdrant and MetadataScope.chunk not in scopes:
            raise ValueError("Qdrant fields must allow chunk scope")
        if self.qdrant_required and MetadataScope.chunk not in scopes:
            raise ValueError("qdrant_required fields must allow chunk scope")
        if self.type not in {MetadataType.enum, MetadataType.list} and self.values:
            raise ValueError("values are only allowed for enum or list fields")
        if self.values_owner is ValuesOwner.none and self.values is not None:
            raise ValueError("values_owner none requires values to be null")
        if self.values_owner is ValuesOwner.core and not self.values:
            raise ValueError("values_owner core requires non-empty values")
        if self.type is MetadataType.enum and self.values_owner is ValuesOwner.core:
            return self
        if self.type is MetadataType.enum and self.values_owner is ValuesOwner.none:
            raise ValueError("enum fields require values_owner core or project")
        return self


class MetadataRegistry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    fields: dict[str, MetadataFieldDefinition] = Field(min_length=1)

    @field_validator("fields")
    @classmethod
    def validate_field_names(
        cls,
        fields: dict[str, MetadataFieldDefinition],
    ) -> dict[str, MetadataFieldDefinition]:
        for name in fields:
            if not name or name.strip() != name:
                raise ValueError("metadata field names must be non-empty and trimmed")
        return fields


class MetadataFieldOverride(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    values: list[str] | None = Field(default=None, min_length=1)
    description: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def require_change(self) -> "MetadataFieldOverride":
        if self.values is None and self.description is None:
            raise ValueError("project overrides must define values or description")
        return self


class ProjectMetadataRegistry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    overrides: dict[str, MetadataFieldOverride] = Field(default_factory=dict)
    fields: dict[str, MetadataFieldDefinition] = Field(default_factory=dict)


class _DuplicateKeySafeLoader(yaml.SafeLoader):
    pass


def _construct_mapping(loader, node, deep=False):
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ValueError(f"Duplicate YAML key: {key}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_DuplicateKeySafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping,
)


def _resolve_registry_path(configured_path: str) -> Path:
    path = Path(configured_path)
    return path if path.is_absolute() else API_ROOT / path


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        raw_registry = yaml.load(stream, Loader=_DuplicateKeySafeLoader)

    if not isinstance(raw_registry, dict):
        raise ValueError(f"Metadata registry must be a YAML object: {path}")
    return raw_registry


def load_core_metadata_registry(path: Path) -> MetadataRegistry:
    return MetadataRegistry.model_validate(_load_yaml(path))


def load_project_metadata_registry(path: Path) -> ProjectMetadataRegistry:
    return ProjectMetadataRegistry.model_validate(_load_yaml(path))


def merge_metadata_registries(
    core_registry: MetadataRegistry,
    project_registry: ProjectMetadataRegistry,
) -> MetadataRegistry:
    fields = dict(core_registry.fields)

    for name, override in project_registry.overrides.items():
        core_field = fields.get(name)
        if core_field is None:
            raise ValueError(f"Project override targets unknown core field: {name}")
        updates = {}
        if override.values is not None and core_field.values_owner is not ValuesOwner.project:
            raise ValueError(f"Core field does not allow project values: {name}")
        if override.values is not None:
            updates["values"] = override.values
        if override.description is not None:
            updates["description"] = override.description
        fields[name] = core_field.model_copy(update=updates)

    for name, project_field in project_registry.fields.items():
        if name in fields:
            raise ValueError(f"Project field conflicts with core field: {name}")
        if project_field.kind is not MetadataKind.project_business:
            raise ValueError("Project fields must use kind project_business")
        if project_field.values_owner is not ValuesOwner.project:
            raise ValueError("Project fields must use values_owner project")
        if project_field.type is MetadataType.enum and not project_field.values:
            raise ValueError("Project enum fields require non-empty values")
        fields[name] = project_field

    return MetadataRegistry(fields=fields)


def load_metadata_registry(
    core_path: Path,
    project_path: Path,
) -> MetadataRegistry:
    return merge_metadata_registries(
        load_core_metadata_registry(core_path),
        load_project_metadata_registry(project_path),
    )


def _configured_registry_paths() -> tuple[Path, Path]:
    config = get_project_config().documentary.metadata_registry
    return (
        _resolve_registry_path(config.core),
        _resolve_registry_path(config.project),
    )


@lru_cache(maxsize=1)
def get_metadata_registry() -> MetadataRegistry:
    core_path, project_path = _configured_registry_paths()
    return load_metadata_registry(core_path, project_path)
