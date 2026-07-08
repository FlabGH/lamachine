from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EnrichmentStage(str, Enum):
    pre_chunking = "pre_chunking"
    post_chunking = "post_chunking"


@dataclass(frozen=True)
class EnricherInfo:
    name: str
    version: str
    description: str
    stages: list[EnrichmentStage]
    enabled_by_default: bool = False
    produces_metadata: bool = False
    produces_structured_objects: bool = False


class EnricherConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    enabled: bool = False
    stages: list[EnrichmentStage]
    parameters: dict[str, Any] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("enricher name must not be empty")
        return normalized

    @field_validator("stages")
    @classmethod
    def reject_empty_stages(cls, value: list[EnrichmentStage]) -> list[EnrichmentStage]:
        if not value:
            raise ValueError("enricher stages must not be empty")
        if len(value) != len(set(value)):
            raise ValueError("enricher stages must not contain duplicates")
        return value


@dataclass(frozen=True)
class DocumentEnrichmentContext:
    document_id: str
    source_id: str
    source_code: str
    title: str
    raw_text: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class ChunkEnrichmentContext:
    document_id: str
    chunk_id: str
    chunk_index: int
    content: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class EnrichmentResult:
    metadata_updates: dict[str, Any] = field(default_factory=dict)
    trace: dict[str, Any] = field(default_factory=dict)


class DocumentaryEnricher(Protocol):
    info: EnricherInfo

    def enrich_document(
        self,
        context: DocumentEnrichmentContext,
        *,
        config: EnricherConfig,
    ) -> EnrichmentResult:
        ...

    def enrich_chunk(
        self,
        context: ChunkEnrichmentContext,
        *,
        config: EnricherConfig,
    ) -> EnrichmentResult:
        ...


class NoopDocumentaryEnricher:
    info = EnricherInfo(
        name="noop_enricher_v1",
        version="1",
        description="No-op documentary enricher used to validate enrichment wiring.",
        stages=[EnrichmentStage.pre_chunking, EnrichmentStage.post_chunking],
        enabled_by_default=False,
        produces_metadata=False,
        produces_structured_objects=False,
    )

    def enrich_document(
        self,
        context: DocumentEnrichmentContext,
        *,
        config: EnricherConfig,
    ) -> EnrichmentResult:
        return EnrichmentResult(
            trace={
                "target": "document",
                "document_id": context.document_id,
                "metadata_updates": [],
            }
        )

    def enrich_chunk(
        self,
        context: ChunkEnrichmentContext,
        *,
        config: EnricherConfig,
    ) -> EnrichmentResult:
        return EnrichmentResult(
            trace={
                "target": "chunk",
                "chunk_id": context.chunk_id,
                "metadata_updates": [],
            }
        )


ENRICHERS: dict[str, DocumentaryEnricher] = {
    NoopDocumentaryEnricher.info.name: NoopDocumentaryEnricher(),
}


def get_enricher(name: str) -> DocumentaryEnricher:
    normalized_name = name.strip()
    try:
        return ENRICHERS[normalized_name]
    except KeyError as exc:
        raise ValueError(f"Unsupported documentary enricher: {name}") from exc


def list_enrichers() -> list[EnricherInfo]:
    return [enricher.info for enricher in ENRICHERS.values()]


def _merge_metadata(
    current_metadata: dict[str, Any],
    metadata_updates: dict[str, Any],
    *,
    enricher_name: str,
) -> dict[str, Any]:
    enriched = dict(current_metadata)
    for name, value in metadata_updates.items():
        if name in enriched and enriched[name] != value:
            raise ValueError(
                "Enricher metadata conflict: "
                f"{enricher_name} attempted to overwrite {name}"
            )
        enriched[name] = value
    return enriched


def _trace_item(
    *,
    config: EnricherConfig,
    stage: EnrichmentStage,
    result: EnrichmentResult,
) -> dict[str, Any]:
    enricher = get_enricher(config.name)
    return {
        "name": enricher.info.name,
        "version": enricher.info.version,
        "stage": stage.value,
        "metadata_updates": sorted(result.metadata_updates),
        "trace": result.trace,
    }


def run_document_enrichers(
    context: DocumentEnrichmentContext,
    *,
    configs: list[EnricherConfig],
    stage: EnrichmentStage = EnrichmentStage.pre_chunking,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    metadata = dict(context.metadata)
    trace: list[dict[str, Any]] = []
    for config in configs:
        if not config.enabled or stage not in config.stages:
            continue
        enricher = get_enricher(config.name)
        result = enricher.enrich_document(
            DocumentEnrichmentContext(
                document_id=context.document_id,
                source_id=context.source_id,
                source_code=context.source_code,
                title=context.title,
                raw_text=context.raw_text,
                metadata=metadata,
            ),
            config=config,
        )
        metadata = _merge_metadata(
            metadata,
            result.metadata_updates,
            enricher_name=config.name,
        )
        trace.append(_trace_item(config=config, stage=stage, result=result))
    return metadata, trace


def run_chunk_enrichers(
    context: ChunkEnrichmentContext,
    *,
    configs: list[EnricherConfig],
    stage: EnrichmentStage = EnrichmentStage.post_chunking,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    metadata = dict(context.metadata)
    trace: list[dict[str, Any]] = []
    for config in configs:
        if not config.enabled or stage not in config.stages:
            continue
        enricher = get_enricher(config.name)
        result = enricher.enrich_chunk(
            ChunkEnrichmentContext(
                document_id=context.document_id,
                chunk_id=context.chunk_id,
                chunk_index=context.chunk_index,
                content=context.content,
                metadata=metadata,
            ),
            config=config,
        )
        metadata = _merge_metadata(
            metadata,
            result.metadata_updates,
            enricher_name=config.name,
        )
        trace.append(_trace_item(config=config, stage=stage, result=result))
    return metadata, trace
