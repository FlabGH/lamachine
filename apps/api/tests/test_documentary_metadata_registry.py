from app.api.documentary import LEXICAL_SEARCH_TEXT_SQL
from app.services.documentary.metadata_contract import (
    CRITICAL_CHUNK_METADATA_KEYS,
    DOCUMENT_METADATA_KEYS,
)
from app.services.documentary.metadata_registry import (
    ALLOWED_LEVELS,
    ALLOWED_STORAGES,
    ALLOWED_USES,
    EXPORT_COLUMNS,
    METADATA_REGISTRY,
    METADATA_REGISTRY_BY_NAME,
    QDRANT_REQUIRED_METADATA,
)


def test_registry_metadata_names_are_unique():
    names = [entry.metadata for entry in METADATA_REGISTRY]

    assert len(names) == len(set(names))


def test_registry_levels_are_allowed():
    invalid = [
        entry.metadata
        for entry in METADATA_REGISTRY
        if entry.level not in ALLOWED_LEVELS
    ]

    assert invalid == []


def test_registry_storage_values_are_allowed():
    invalid = [
        (entry.metadata, storage)
        for entry in METADATA_REGISTRY
        for storage in entry.storage
        if storage not in ALLOWED_STORAGES
    ]

    assert invalid == []


def test_registry_uses_are_allowed():
    invalid = [
        (entry.metadata, use)
        for entry in METADATA_REGISTRY
        for use in entry.uses
        if use not in ALLOWED_USES
    ]

    assert invalid == []


def test_qdrant_propagation_requires_chunk_metadata_or_documented_exception():
    invalid = [
        entry.metadata
        for entry in METADATA_REGISTRY
        if entry.propagate_to_qdrant
        and not entry.propagate_to_chunk
        and not entry.qdrant_without_chunk_reason
    ]

    assert invalid == []


def test_qdrant_required_fields_are_strict_and_minimal():
    qdrant_required = {
        entry.metadata
        for entry in METADATA_REGISTRY
        if entry.qdrant_required
    }

    assert qdrant_required == QDRANT_REQUIRED_METADATA
    assert "vector_collection" not in qdrant_required


def test_deprecated_chunking_aliases_are_documented():
    expected_aliases = {
        "chunking_strategy": "chunking_version",
        "chunk_size_words": "chunk_size",
        "chunk_overlap_words": "chunk_overlap",
    }

    for alias, canonical in expected_aliases.items():
        entry = METADATA_REGISTRY_BY_NAME[alias]
        assert entry.deprecated is True
        assert entry.alias_of == canonical


def test_document_contract_keys_are_registered():
    missing = [
        key
        for key in sorted(DOCUMENT_METADATA_KEYS)
        if key not in METADATA_REGISTRY_BY_NAME
    ]

    assert missing == []


def test_critical_chunk_metadata_keys_are_registered():
    missing = [
        key
        for key in sorted(CRITICAL_CHUNK_METADATA_KEYS)
        if key not in METADATA_REGISTRY_BY_NAME
    ]

    assert missing == []


def test_limited_extraction_metadata_scope_is_registered():
    extraction_keys = {
        "extraction",
        "extracted_pages",
        "extraction.status",
        "extraction.ocr_used",
        "extraction.page_count",
        "extraction.layout_quality_status",
        "extraction.errors",
    }

    assert extraction_keys <= set(METADATA_REGISTRY_BY_NAME)

    unexpected_exhaustive_keys = {
        "extraction.ocr_provider",
        "extraction.ocr_model",
        "extraction.warnings",
        "extracted_pages[].text",
    }

    assert unexpected_exhaustive_keys.isdisjoint(METADATA_REGISTRY_BY_NAME)


def test_lexical_metadata_fields_are_registered_as_retrieval_used():
    lexical_metadata = {
        "source_code",
        "document_title",
        "role_documentaire",
        "theme_tags",
    }

    for metadata in lexical_metadata:
        assert metadata in LEXICAL_SEARCH_TEXT_SQL
        entry = METADATA_REGISTRY_BY_NAME[metadata]
        assert "retrieval" in entry.uses


def test_markdown_export_header_and_entries_match_registry():
    export_path = "docs/phase3_metadata_registry.md"
    with open(export_path, encoding="utf-8") as handle:
        lines = handle.readlines()

    table_header = next(
        line for line in lines if line.startswith("| Metadata | level | storage |")
    )
    exported_columns = tuple(
        column.strip()
        for column in table_header.strip().strip("|").split("|")
    )
    assert exported_columns == EXPORT_COLUMNS

    exported_names = {
        line.split("|", maxsplit=2)[1].strip().strip("`")
        for line in lines
        if line.startswith("| `")
    }

    assert exported_names == set(METADATA_REGISTRY_BY_NAME)
