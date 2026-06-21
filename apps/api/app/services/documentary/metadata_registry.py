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
    values: list[str] | None = None

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
        if self.type is MetadataType.enum and not self.values:
            raise ValueError("enum fields must define non-empty values")
        if self.type is not MetadataType.enum and self.values is not None:
            raise ValueError("values are only allowed for enum fields")
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


def _resolve_metadata_registry_path() -> Path:
    configured_path = get_project_config().documentary.metadata_registry.strip()
    path = Path(configured_path)
    return path if path.is_absolute() else API_ROOT / path


def load_metadata_registry(path: Path | None = None) -> MetadataRegistry:
    registry_path = path or _resolve_metadata_registry_path()
    with registry_path.open("r", encoding="utf-8") as stream:
        raw_registry = yaml.load(stream, Loader=_DuplicateKeySafeLoader)

    if not isinstance(raw_registry, dict):
        raise ValueError(f"Metadata registry must be a YAML object: {registry_path}")
    return MetadataRegistry.model_validate(raw_registry)


@lru_cache(maxsize=1)
def get_metadata_registry() -> MetadataRegistry:
    return load_metadata_registry()
