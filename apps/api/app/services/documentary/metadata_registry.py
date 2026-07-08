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


class ProjectInputPolicy(str, Enum):
    required = "required"
    optional = "optional"
    forbidden = "forbidden"


class MetadataScope(str, Enum):
    document = "document"
    chunk = "chunk"
    run = "run"
    model_call = "model_call"
    retrieval_hit = "retrieval_hit"


class MetadataPresentationGroup(str, Enum):
    project = "project"
    description = "description"
    classification = "classification"
    source = "source"
    retrieval = "retrieval"
    rights = "rights"
    audit = "audit"
    technical = "technical"


class MetadataPresentationImportance(str, Enum):
    primary = "primary"
    secondary = "secondary"
    advanced = "advanced"


class MetadataPresentationWidget(str, Enum):
    text = "text"
    textarea = "textarea"
    select = "select"
    multiselect = "multiselect"
    tags = "tags"
    checkbox = "checkbox"
    number = "number"
    date = "date"
    datetime = "datetime"
    json = "json"


class MetadataVisibilityContext(str, Enum):
    ingestion = "ingestion"
    search = "search"
    document = "document"
    chunk = "chunk"
    catalog = "catalog"


def _default_widget(metadata_type: str | MetadataType) -> str:
    value = metadata_type.value if isinstance(metadata_type, MetadataType) else metadata_type
    return {
        MetadataType.enum.value: MetadataPresentationWidget.select.value,
        MetadataType.free.value: MetadataPresentationWidget.text.value,
        MetadataType.boolean.value: MetadataPresentationWidget.checkbox.value,
        MetadataType.number.value: MetadataPresentationWidget.number.value,
        MetadataType.integer.value: MetadataPresentationWidget.number.value,
        MetadataType.date.value: MetadataPresentationWidget.date.value,
        MetadataType.datetime.value: MetadataPresentationWidget.datetime.value,
        MetadataType.object.value: MetadataPresentationWidget.json.value,
        MetadataType.list.value: MetadataPresentationWidget.tags.value,
    }.get(value, MetadataPresentationWidget.text.value)


def _default_visibility(data: dict[str, Any]) -> list[str]:
    contexts = {MetadataVisibilityContext.catalog.value}
    if data.get("project_input") in {
        ProjectInputPolicy.required.value,
        ProjectInputPolicy.optional.value,
    }:
        contexts.add(MetadataVisibilityContext.ingestion.value)
    if data.get("retrieval_filterable") is True:
        contexts.add(MetadataVisibilityContext.search.value)
    scopes = set(data.get("scopes") or [])
    if MetadataScope.document.value in scopes:
        contexts.add(MetadataVisibilityContext.document.value)
    if MetadataScope.chunk.value in scopes:
        contexts.add(MetadataVisibilityContext.chunk.value)
    return [
        context.value
        for context in MetadataVisibilityContext
        if context.value in contexts
    ]


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
    project_input: ProjectInputPolicy
    values_owner: ValuesOwner
    values: list[str] | None = None
    description: str = Field(min_length=1)
    presentation_group: MetadataPresentationGroup = MetadataPresentationGroup.technical
    presentation_order: int = Field(default=999, ge=0)
    presentation_importance: MetadataPresentationImportance = (
        MetadataPresentationImportance.secondary
    )
    presentation_widget: MetadataPresentationWidget
    visible_in: list[MetadataVisibilityContext]

    @model_validator(mode="before")
    @classmethod
    def apply_presentation_defaults(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        normalized = dict(data)
        if normalized.get("presentation_widget") is None:
            normalized["presentation_widget"] = _default_widget(normalized.get("type"))
        if normalized.get("visible_in") is None:
            normalized["visible_in"] = _default_visibility(normalized)
        return normalized

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

    @field_validator("visible_in")
    @classmethod
    def reject_duplicate_visibility_contexts(
        cls,
        visible_in: list[MetadataVisibilityContext],
    ) -> list[MetadataVisibilityContext]:
        if len(visible_in) != len(set(visible_in)):
            raise ValueError("visible_in must not contain duplicates")
        return visible_in

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
        if self.retrieval_filterable and MetadataScope.chunk not in scopes:
            raise ValueError("retrieval_filterable fields must allow chunk scope")
        if self.retrieval_filterable and not self.propagate_to_qdrant:
            raise ValueError(
                "retrieval_filterable fields must propagate_to_qdrant"
            )
        if (
            self.project_input is not ProjectInputPolicy.forbidden
            and MetadataScope.document not in scopes
        ):
            raise ValueError(
                "project_input required or optional fields must allow document scope"
            )
        if (
            self.project_input is ProjectInputPolicy.required
            and not self.required
        ):
            raise ValueError("project_input required fields must be required")
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
    presentation_group: MetadataPresentationGroup | None = None
    presentation_order: int | None = Field(default=None, ge=0)
    presentation_importance: MetadataPresentationImportance | None = None
    presentation_widget: MetadataPresentationWidget | None = None
    visible_in: list[MetadataVisibilityContext] | None = None

    @field_validator("visible_in")
    @classmethod
    def reject_duplicate_visibility_contexts(
        cls,
        visible_in: list[MetadataVisibilityContext] | None,
    ) -> list[MetadataVisibilityContext] | None:
        if visible_in is not None and len(visible_in) != len(set(visible_in)):
            raise ValueError("visible_in must not contain duplicates")
        return visible_in

    @model_validator(mode="after")
    def require_change(self) -> "MetadataFieldOverride":
        if not any(
            value is not None
            for value in (
                self.values,
                self.description,
                self.presentation_group,
                self.presentation_order,
                self.presentation_importance,
                self.presentation_widget,
                self.visible_in,
            )
        ):
            raise ValueError(
                "project overrides must define values, description, "
                "or presentation attributes"
            )
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
        for attribute in (
            "presentation_group",
            "presentation_order",
            "presentation_importance",
            "presentation_widget",
            "visible_in",
        ):
            value = getattr(override, attribute)
            if value is not None:
                updates[attribute] = value
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
