from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any


CRITICAL_CHUNK_METADATA_KEYS = {
    "source_id",
    "document_id",
    "chunk_id",
    "title",
    "source_code",
    "content_hash",
    "index_version",
    "vector_collection",
    "chunk_index",
    "token_count",
    "chunking_version",
    "chunking_strategy",
    "chunk_size",
    "chunk_overlap",
}


def _normalize_required_text(metadata: dict[str, Any], key: str) -> str:
    value = metadata.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Missing or invalid document metadata key: {key}")
    return value.strip()


def _normalize_optional_text(metadata: dict[str, Any], key: str) -> str | None:
    value = metadata.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"Invalid document metadata key: {key}")
    normalized = value.strip()
    return normalized or None


def _normalize_optional_string_list(
    metadata: dict[str, Any],
    key: str,
    *,
    default: list[str],
) -> list[str]:
    value = metadata.get(key)
    if value is None:
        return list(default)
    if not isinstance(value, list):
        raise ValueError(f"Invalid document metadata key: {key}")

    normalized_items = []
    for item in value:
        if not isinstance(item, str):
            raise ValueError(f"{key} must contain only strings")
        normalized = item.strip()
        if normalized:
            normalized_items.append(normalized)
    return normalized_items


def _normalize_optional_bool(
    metadata: dict[str, Any],
    key: str,
    default: bool,
) -> bool:
    value = metadata.get(key)
    if value is None:
        return default
    if not isinstance(value, bool):
        raise ValueError(f"Invalid document metadata key: {key}")
    return value


def _normalize_optional_iso_date_text(metadata: dict[str, Any], key: str) -> str | None:
    value = metadata.get(key)
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Invalid document metadata key: {key}")

    raw_value = value.strip()
    try:
        if "T" in raw_value:
            return datetime.fromisoformat(raw_value.replace("Z", "+00:00")).isoformat()
        return date.fromisoformat(raw_value).isoformat()
    except ValueError as exc:
        raise ValueError(f"Invalid ISO date metadata key: {key}") from exc


def normalize_document_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    title = _normalize_required_text(metadata, "title")
    source_code = _normalize_required_text(metadata, "source_code").lower()
    theme_tags = _normalize_optional_string_list(
        metadata,
        "theme_tags",
        default=[],
    )
    return {
        **normalize_ingestion_metadata(
            metadata,
            title=title,
            source_code=source_code,
        ),
        "theme_tags": theme_tags,
    }


def normalize_ingestion_metadata(
    metadata: dict[str, Any] | None,
    *,
    title: str | None = None,
    source_code: str | None = None,
) -> dict[str, Any]:
    source = metadata or {}
    normalized: dict[str, Any] = {
        "data_tags": _normalize_optional_string_list(
            source,
            "data_tags",
            default=[],
        ),
        "theme_tags": _normalize_optional_string_list(
            source,
            "theme_tags",
            default=[],
        ),
        "visibility_scope": _normalize_optional_text(source, "visibility_scope"),
        "organization_id": _normalize_optional_text(source, "organization_id"),
        "access_level": _normalize_optional_text(source, "access_level"),
        "source_url": _normalize_optional_text(source, "source_url"),
        "publication_date": _normalize_optional_iso_date_text(source, "publication_date"),
        "collected_at": _normalize_optional_iso_date_text(source, "collected_at")
        or datetime.now(UTC).isoformat(),
        "language": _normalize_optional_text(source, "language"),
        "geographic_scope": _normalize_optional_text(source, "geographic_scope"),
        "temporal_scope": _normalize_optional_text(source, "temporal_scope"),
        "is_primary_source": _normalize_optional_bool(
            source,
            "is_primary_source",
            False,
        ),
        "citation_policy": _normalize_optional_text(source, "citation_policy"),
        "rights_status": _normalize_optional_text(source, "rights_status"),
    }

    if title is not None:
        normalized["title"] = title.strip() if title.strip() else title
    if source_code is not None:
        normalized["source_code"] = source_code.strip().lower()

    return {key: value for key, value in normalized.items() if value is not None}


def build_chunk_metadata(
    *,
    source_id: Any,
    document_id: Any,
    chunk_id: Any,
    title: str,
    source_code: str,
    content_hash: str,
    index_version: Any,
    vector_collection: str,
    chunk_index: int,
    token_count: int,
    chunking_version: str,
    chunking_strategy: str,
    chunk_size: int,
    chunk_overlap: int,
    parent_document_id: Any | None = None,
    page_start: int | None = None,
    page_end: int | None = None,
    section_title: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return build_canonical_chunk_metadata(
        source_id=source_id,
        document_id=document_id,
        chunk_id=chunk_id,
        title=title,
        source_code=source_code,
        content_hash=content_hash,
        index_version=index_version,
        vector_collection=vector_collection,
        chunk_index=chunk_index,
        token_count=token_count,
        chunking_version=chunking_version,
        chunking_strategy=chunking_strategy,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        parent_document_id=parent_document_id,
        page_start=page_start,
        page_end=page_end,
        section_title=section_title,
        extra=extra,
    )


def build_canonical_chunk_metadata(
    *,
    source_id: Any,
    document_id: Any,
    chunk_id: Any,
    title: str,
    source_code: str,
    content_hash: str,
    index_version: Any,
    vector_collection: str,
    chunk_index: int,
    token_count: int,
    chunking_version: str,
    chunking_strategy: str,
    chunk_size: int,
    chunk_overlap: int,
    parent_document_id: Any | None = None,
    page_start: int | None = None,
    page_end: int | None = None,
    section_title: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metadata = {
        **(extra or {}),
        "source_id": str(source_id),
        "document_id": str(document_id),
        "parent_document_id": str(parent_document_id or document_id),
        "chunk_id": str(chunk_id),
        "title": title,
        "source_code": source_code,
        "content_hash": content_hash,
        "index_version": str(index_version),
        "vector_collection": vector_collection,
        "chunk_index": chunk_index,
        "token_count": token_count,
        "chunking_version": chunking_version,
        "chunking_strategy": chunking_strategy,
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
    }
    if page_start is not None:
        metadata["page_start"] = page_start
    if page_end is not None:
        metadata["page_end"] = page_end
    if section_title:
        metadata["section_title"] = section_title
    return metadata


def missing_chunk_metadata_keys(metadata: dict[str, Any]) -> list[str]:
    return [
        key
        for key in sorted(CRITICAL_CHUNK_METADATA_KEYS)
        if metadata.get(key) in (None, "")
    ]


def validate_chunk_metadata(metadata: dict[str, Any]) -> None:
    missing = missing_chunk_metadata_keys(metadata)
    if missing:
        raise ValueError(f"Missing chunk metadata keys: {', '.join(missing)}")


def build_qdrant_payload(
    *,
    chunk_id: Any,
    chunk_metadata: dict[str, Any],
) -> dict[str, Any]:
    validate_chunk_metadata(chunk_metadata)
    return {
        "chunk_id": str(chunk_id),
        **chunk_metadata,
    }
