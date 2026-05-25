from __future__ import annotations

from typing import Any


CRITICAL_CHUNK_METADATA_KEYS = {
    "source_id",
    "document_id",
    "document_title",
    "source_name",
    "content_sha256",
    "index_version_id",
    "vector_collection",
}


def build_chunk_metadata(
    *,
    source_id: Any,
    document_id: Any,
    document_title: str,
    source_name: str,
    content_sha256: str,
    index_version_id: Any,
    vector_collection: str,
    page_start: int | None = None,
    page_end: int | None = None,
    section: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metadata = {
        **(extra or {}),
        "source_id": str(source_id),
        "document_id": str(document_id),
        "document_title": document_title,
        "source_name": source_name,
        "content_sha256": content_sha256,
        "index_version_id": str(index_version_id),
        "vector_collection": vector_collection,
    }

    if page_start is not None:
        metadata["page_start"] = page_start
    if page_end is not None:
        metadata["page_end"] = page_end

    if page_start is None and page_end is None:
        metadata["section"] = section or "body"
    elif section:
        metadata["section"] = section

    return metadata


def missing_chunk_metadata_keys(metadata: dict[str, Any]) -> list[str]:
    missing = [
        key
        for key in sorted(CRITICAL_CHUNK_METADATA_KEYS)
        if metadata.get(key) in (None, "")
    ]

    has_page = metadata.get("page_start") is not None or metadata.get("page_end") is not None
    has_section = bool(metadata.get("section"))
    if not has_page and not has_section:
        missing.append("page_or_section")

    return missing


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
