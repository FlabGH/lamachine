from __future__ import annotations

import pytest

from app.services.documentary.enrichers import (
    ChunkEnrichmentContext,
    DocumentEnrichmentContext,
    EnricherConfig,
    EnrichmentResult,
    EnrichmentStage,
    get_enricher,
    list_enrichers,
    run_chunk_enrichers,
    run_document_enrichers,
)


class MetadataUpdatingEnricher:
    def __init__(self, metadata_updates):
        self.info = get_enricher("noop_enricher_v1").info
        self.metadata_updates = metadata_updates

    def enrich_document(self, context, *, config):
        return EnrichmentResult(
            metadata_updates=dict(self.metadata_updates),
            trace={"target": "document"},
        )

    def enrich_chunk(self, context, *, config):
        return EnrichmentResult(
            metadata_updates=dict(self.metadata_updates),
            trace={"target": "chunk"},
        )


def _document_context(**metadata):
    return DocumentEnrichmentContext(
        document_id="document-id",
        source_id="source-id",
        source_code="source",
        title="Document",
        raw_text="Texte",
        metadata=metadata,
    )


def _chunk_context(**metadata):
    return ChunkEnrichmentContext(
        document_id="document-id",
        chunk_id="chunk-id",
        chunk_index=0,
        content="Chunk",
        metadata=metadata,
    )


def test_enricher_registry_exposes_noop_enricher():
    names = {enricher.name for enricher in list_enrichers()}

    assert names == {"noop_enricher_v1"}
    assert get_enricher("noop_enricher_v1").info.enabled_by_default is False
    assert get_enricher("noop_enricher_v1").info.stages == [
        EnrichmentStage.pre_chunking,
        EnrichmentStage.post_chunking,
    ]

    with pytest.raises(ValueError, match="Unsupported documentary enricher"):
        get_enricher("unknown_enricher")


def test_enricher_config_requires_stage():
    with pytest.raises(ValueError, match="stages"):
        EnricherConfig(name="noop_enricher_v1", enabled=True, stages=[])


def test_disabled_enricher_is_not_executed():
    metadata, trace = run_document_enrichers(
        _document_context(source_code="source"),
        configs=[
            EnricherConfig(
                name="noop_enricher_v1",
                enabled=False,
                stages=[EnrichmentStage.pre_chunking],
            )
        ],
    )

    assert metadata == {"source_code": "source"}
    assert trace == []


def test_noop_document_enricher_keeps_metadata_and_traces_execution():
    metadata, trace = run_document_enrichers(
        _document_context(source_code="source"),
        configs=[
            EnricherConfig(
                name="noop_enricher_v1",
                enabled=True,
                stages=[EnrichmentStage.pre_chunking],
            )
        ],
    )

    assert metadata == {"source_code": "source"}
    assert trace[0]["name"] == "noop_enricher_v1"
    assert trace[0]["stage"] == "pre_chunking"
    assert trace[0]["metadata_updates"] == []


def test_noop_chunk_enricher_keeps_metadata_and_traces_execution():
    metadata, trace = run_chunk_enrichers(
        _chunk_context(source_code="source"),
        configs=[
            EnricherConfig(
                name="noop_enricher_v1",
                enabled=True,
                stages=[EnrichmentStage.post_chunking],
            )
        ],
    )

    assert metadata == {"source_code": "source"}
    assert trace[0]["name"] == "noop_enricher_v1"
    assert trace[0]["stage"] == "post_chunking"


def test_enricher_metadata_conflict_is_blocking(monkeypatch):
    monkeypatch.setitem(
        __import__(
            "app.services.documentary.enrichers",
            fromlist=["ENRICHERS"],
        ).ENRICHERS,
        "conflicting_enricher_v1",
        MetadataUpdatingEnricher({"source_code": "other"}),
    )

    with pytest.raises(ValueError, match="metadata conflict"):
        run_document_enrichers(
            _document_context(source_code="source"),
            configs=[
                EnricherConfig(
                    name="conflicting_enricher_v1",
                    enabled=True,
                    stages=[EnrichmentStage.pre_chunking],
                )
            ],
        )
