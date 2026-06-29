from __future__ import annotations

from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from dataclasses import dataclass
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.documentary.metadata_registry import get_metadata_registry
from app.services.documentary.metadata_validation import (
    MetadataValidationError,
    MetadataValidationIssue,
    validate_retrieval_filters,
)
from app.services.project_config import API_ROOT, get_project_config


class RerankingStrategy(str, Enum):
    configured_reranker = "configured_reranker"
    none = "none"


class RetrievalPreset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    dense_top_k: int = Field(ge=1)
    lexical_top_k: int = Field(ge=1)
    rerank_top_k: int = Field(ge=1)
    reranking_strategy: RerankingStrategy = RerankingStrategy.configured_reranker
    filters: dict[str, list[Any]] = Field(default_factory=dict)
    trace_parameters: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_filters(self) -> RetrievalPreset:
        self.filters = validate_retrieval_filters(
            self.filters,
            registry=get_metadata_registry(),
        )
        return self


class RetrievalPresetCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    presets: dict[str, RetrievalPreset]

    @model_validator(mode="after")
    def validate_names(self) -> RetrievalPresetCatalog:
        for name, preset in self.presets.items():
            if preset.name != name:
                raise ValueError(
                    f"Retrieval preset key must match preset.name: {name}"
                )
        return self


@dataclass(frozen=True)
class RetrievalPlan:
    preset: RetrievalPreset
    preset_source: str
    dense_top_k: int
    lexical_top_k: int
    rerank_top_k: int
    reranking_strategy: RerankingStrategy
    preset_filters: dict[str, list[Any]]
    request_filters: dict[str, list[Any]]
    filters: dict[str, list[Any]]

    def trace_payload(self) -> dict[str, Any]:
        return {
            "preset": self.preset.name,
            "preset_source": self.preset_source,
            "description": self.preset.description,
            "dense_top_k": self.dense_top_k,
            "lexical_top_k": self.lexical_top_k,
            "rerank_top_k": self.rerank_top_k,
            "reranking_strategy": self.reranking_strategy.value,
            "preset_filters": self.preset_filters,
            "request_filters": self.request_filters,
            "metadata_filters": self.filters,
            "trace_parameters": self.preset.trace_parameters,
        }


def _resolve_retrieval_presets_path(path: str | Path | None = None) -> Path:
    if path is not None:
        configured_path = Path(path)
    else:
        configured_path = Path(get_project_config().documentary.retrieval_presets)

    if configured_path.is_absolute():
        return configured_path
    return API_ROOT / configured_path


def load_retrieval_preset_catalog(
    path: str | Path | None = None,
) -> RetrievalPresetCatalog:
    catalog_path = _resolve_retrieval_presets_path(path)
    with catalog_path.open("r", encoding="utf-8") as stream:
        raw_catalog: Any = yaml.safe_load(stream)

    if not isinstance(raw_catalog, dict):
        raise ValueError(f"Retrieval preset catalog must be a YAML object: {catalog_path}")

    return RetrievalPresetCatalog.model_validate(raw_catalog)


@lru_cache(maxsize=1)
def get_retrieval_preset_catalog() -> RetrievalPresetCatalog:
    return load_retrieval_preset_catalog()


def list_retrieval_presets() -> list[RetrievalPreset]:
    return list(get_retrieval_preset_catalog().presets.values())


def get_retrieval_preset(name: str | None = None) -> RetrievalPreset:
    preset_name = name or get_project_config().documentary.retrieval_preset
    catalog = get_retrieval_preset_catalog()
    try:
        return catalog.presets[preset_name]
    except KeyError as exc:
        raise ValueError(f"Retrieval preset not found: {preset_name}") from exc


def _merge_retrieval_filters(
    *,
    preset_filters: dict[str, list[Any]],
    request_filters: dict[str, list[Any]],
) -> dict[str, list[Any]]:
    merged = {field: list(values) for field, values in preset_filters.items()}
    issues: list[MetadataValidationIssue] = []

    for field, values in request_filters.items():
        if field not in merged:
            merged[field] = list(values)
            continue
        if merged[field] != values:
            issues.append(
                MetadataValidationIssue(
                    code="filter_conflict",
                    field=field,
                    message=(
                        "Request filter conflicts with the retrieval preset filter"
                    ),
                )
            )

    if issues:
        raise MetadataValidationError(issues)
    return merged


def resolve_retrieval_plan(
    *,
    requested_preset: str | None,
    request_fields: set[str],
    request_top_k: int,
    request_rerank_top_k: int,
    request_filters: dict[str, list[Any]],
) -> RetrievalPlan:
    preset = get_retrieval_preset(requested_preset)
    registry = get_metadata_registry()
    validated_request_filters = validate_retrieval_filters(
        request_filters,
        registry=registry,
    )
    merged_filters = validate_retrieval_filters(
        _merge_retrieval_filters(
            preset_filters=preset.filters,
            request_filters=validated_request_filters,
        ),
        registry=registry,
    )
    top_k_overridden = "top_k" in request_fields
    rerank_top_k_overridden = "rerank_top_k" in request_fields

    return RetrievalPlan(
        preset=preset,
        preset_source="request" if requested_preset else "project_config",
        dense_top_k=request_top_k if top_k_overridden else preset.dense_top_k,
        lexical_top_k=request_top_k if top_k_overridden else preset.lexical_top_k,
        rerank_top_k=(
            request_rerank_top_k
            if rerank_top_k_overridden
            else preset.rerank_top_k
        ),
        reranking_strategy=preset.reranking_strategy,
        preset_filters=preset.filters,
        request_filters=validated_request_filters,
        filters=merged_filters,
    )
