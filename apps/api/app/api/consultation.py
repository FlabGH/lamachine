from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from app.api.documentary import (
    SearchMetadataFilters,
    SearchRequest as DocumentarySearchRequest,
    _default_rerank_top_k,
    _default_search_top_k,
    search_documents as documentary_search_documents,
)
from app.db import get_connection
from app.services.documentary.metadata_registry import METADATA_REGISTRY
from app.services.documentary.vector_store import get_qdrant_client


router = APIRouter(prefix="/v1", tags=["consultation"])

MAX_LIMIT = 100
DEFAULT_LIMIT = 50
SENSITIVE_METADATA_KEYS = {"extraction", "extracted_pages"}
SENSITIVE_TRACE_KEYS = {
    "messages",
    "prompt",
    "response_metadata",
    "raw",
    "raw_response",
}
IMPLEMENTED_SEARCH_FILTERS = {
    entry.metadata
    for entry in METADATA_REGISTRY
    if entry.retrieval_filterable and entry.implementation_status == "implemented"
}
LIST_SEARCH_FILTERS = {"theme_tags", "data_tags", "service_ids"}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PaginatedResponse(StrictModel):
    limit: int
    offset: int
    total: int


class MetadataCatalogItem(StrictModel):
    metadata: str
    level: str
    description: str
    uses: list[str]
    implementation_status: str
    allowed_values: list[str] | None = None
    default_value: Any | None = None
    retrieval_filterable: bool
    qdrant_required: bool
    alias_of: str | None = None
    deprecated: bool


class MetadataCatalogResponse(StrictModel):
    items: list[MetadataCatalogItem]


class SearchFilterSemantics(StrictModel):
    between_fields: str
    within_field_values: str
    list_fields: list[str]
    invalid_filters: str


class SearchCapabilitiesResponse(StrictModel):
    retrieval: dict[str, bool]
    filter_semantics: SearchFilterSemantics
    implemented_filters: list[MetadataCatalogItem]
    planned_filters: list[MetadataCatalogItem]
    display_only_metadata: list[MetadataCatalogItem]


class IndexVersionRead(StrictModel):
    id: UUID
    name: str
    embedding_provider: str
    embedding_model: str
    embedding_dimension: int
    vector_collection: str
    chunking_version: str
    split_strategy: str
    chunk_size: int
    chunk_overlap: int
    min_chunk_size: int
    max_chunk_size: int
    is_active: bool
    created_at: datetime | None = None


class IndexVersionListResponse(PaginatedResponse):
    items: list[IndexVersionRead]


class PromoteIndexVersionResponse(StrictModel):
    index_version_id: UUID
    is_active: bool
    vector_collection: str
    chunk_count: int
    qdrant_point_count: int
    warnings: list[str] = Field(default_factory=list)


class SourceSummary(StrictModel):
    source_id: UUID
    source_code: str
    source_type: str
    origin: str | None = None
    author: str | None = None
    published_at: datetime | None = None
    document_count: int
    chunk_count: int


class SourceListResponse(PaginatedResponse):
    items: list[SourceSummary]


class SourceDetail(SourceSummary):
    pass


class DocumentSummary(StrictModel):
    document_id: UUID
    source_id: UUID
    source_code: str
    title: str
    filename: str | None = None
    mime_type: str
    status: str
    created_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    chunk_count: int


class DocumentListResponse(PaginatedResponse):
    items: list[DocumentSummary]


class DocumentDetail(DocumentSummary):
    pass


class ChunkSummary(StrictModel):
    chunk_id: UUID
    document_id: UUID
    index_version_id: UUID
    chunk_index: int
    page_start: int | None = None
    page_end: int | None = None
    token_count: int | None = None
    content: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChunkListResponse(PaginatedResponse):
    items: list[ChunkSummary]


class ChunkDetail(ChunkSummary):
    pass


class ExtractedPageRead(StrictModel):
    page: int
    text: str | None = None
    char_count: int
    section_title: str | None = None
    extraction_source: str = "pypdf"
    layout_quality: dict[str, Any] = Field(default_factory=dict)


class DocumentExtractionRead(StrictModel):
    document_id: UUID
    title: str
    extraction: dict[str, Any] = Field(default_factory=dict)
    pages: list[ExtractedPageRead]
    page_from: int | None = None
    page_to: int | None = None
    total_pages: int


class RunDetail(StrictModel):
    run_id: UUID
    run_type: str
    status: str
    index_version_id: UUID | None = None
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class RetrievalHitDetail(StrictModel):
    retrieval_hit_id: UUID
    run_id: UUID
    chunk_id: UUID
    document_id: UUID
    rank_initial: int | None = None
    rank_final: int | None = None
    dense_score: float | None = None
    lexical_score: float | None = None
    rerank_score: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalHitListResponse(PaginatedResponse):
    items: list[RetrievalHitDetail]


class StableSearchRequest(StrictModel):
    query: str
    index_version_id: UUID
    top_k: int = Field(default_factory=_default_search_top_k, ge=1, le=100)
    rerank_top_k: int = Field(default_factory=_default_rerank_top_k, ge=1, le=100)
    filters: SearchMetadataFilters | None = None


class StableSearchHit(StrictModel):
    chunk_id: UUID
    document_id: UUID
    rank_initial: int | None = None
    rank_final: int
    score: float | None = None
    dense_score: float | None = None
    lexical_score: float | None = None
    rerank_score: float | None = None
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class StableSearchResponse(StrictModel):
    run_id: UUID
    index_version_id: UUID
    filters_applied: dict[str, list[str]] = Field(default_factory=dict)
    hits: list[StableSearchHit]


def _metadata_description(metadata: str) -> str:
    descriptions = {
        "source_code": "Identifiant court et canonique de la source.",
        "role_documentaire": "Role documentaire ou epistemique de la source.",
        "theme_tags": "Tags thematiques associes au document.",
        "data_tags": "Categories de donnees mobilisees ou necessaires.",
        "service_family": "Famille de service LaMachine concernee.",
        "service_ids": "Identifiants de services concernes.",
        "visibility_scope": "Perimetre de visibilite du document.",
        "organization_id": "Organisation proprietaire du document.",
        "access_level": "Niveau d'acces fonctionnel.",
        "language": "Langue principale du document.",
    }
    return descriptions.get(metadata, metadata.replace("_", " "))


def _entry_to_catalog_item(entry) -> MetadataCatalogItem:
    return MetadataCatalogItem(
        metadata=entry.metadata,
        level=entry.level,
        description=entry.description or _metadata_description(entry.metadata),
        uses=list(entry.uses),
        implementation_status=entry.implementation_status,
        allowed_values=list(entry.allowed_values) if entry.allowed_values else None,
        default_value=entry.default_value,
        retrieval_filterable=entry.retrieval_filterable,
        qdrant_required=entry.qdrant_required,
        alias_of=entry.alias_of,
        deprecated=entry.deprecated,
    )


def _bounded_limit(limit: int) -> int:
    return min(max(limit, 1), MAX_LIMIT)


def _safe_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    if not metadata:
        return {}
    return {
        key: value
        for key, value in metadata.items()
        if key not in SENSITIVE_METADATA_KEYS
    }


def _safe_trace_payload(payload: dict[str, Any] | None) -> dict[str, Any]:
    if not payload:
        return {}
    safe: dict[str, Any] = {}
    for key, value in payload.items():
        if key in SENSITIVE_TRACE_KEYS:
            continue
        if isinstance(value, dict):
            safe[key] = _safe_trace_payload(value)
        elif isinstance(value, list):
            safe[key] = [
                _safe_trace_payload(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            safe[key] = value
    return safe


def _total(row: dict[str, Any] | None) -> int:
    if not row:
        return 0
    return int(row.get("total_count") or 0)


def _without_total_count(row: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in row.items()
        if key != "total_count"
    }


def _source_from_row(row: dict[str, Any]) -> SourceSummary:
    return SourceSummary(**_without_total_count(row))


def _fetch_retrieval_score_rows(run_id: UUID) -> dict[UUID, dict[str, Any]]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    chunk_id,
                    rank_initial,
                    rank_final,
                    dense_score,
                    lexical_score,
                    rerank_score
                FROM retrieval_hits
                WHERE run_id = %s
                """,
                (run_id,),
            )
            rows = cur.fetchall()
    return {row["chunk_id"]: row for row in rows}


def _qdrant_point_count(collection_name: str) -> int:
    try:
        return int(
            get_qdrant_client()
            .count(collection_name=collection_name, exact=True)
            .count
        )
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "qdrant_unavailable",
                "message": "Unable to verify Qdrant collection before promotion",
            },
        ) from exc


@router.get("/metadata/catalog", response_model=MetadataCatalogResponse)
def get_metadata_catalog(
    level: str | None = None,
    retrieval_filterable: bool | None = None,
) -> MetadataCatalogResponse:
    items = []
    for entry in METADATA_REGISTRY:
        if level is not None and entry.level != level:
            continue
        if (
            retrieval_filterable is not None
            and entry.retrieval_filterable is not retrieval_filterable
        ):
            continue
        items.append(_entry_to_catalog_item(entry))
    return MetadataCatalogResponse(items=items)


@router.get("/search/capabilities", response_model=SearchCapabilitiesResponse)
def get_search_capabilities() -> SearchCapabilitiesResponse:
    catalog_items = [_entry_to_catalog_item(entry) for entry in METADATA_REGISTRY]
    implemented = [
        item for item in catalog_items
        if item.retrieval_filterable and item.implementation_status == "implemented"
    ]
    planned = [
        item for item in catalog_items
        if item.retrieval_filterable and item.implementation_status != "implemented"
    ]
    display_only = [
        item for item in catalog_items
        if not item.retrieval_filterable
        and ("display" in item.uses or "audit" in item.uses)
    ]
    return SearchCapabilitiesResponse(
        retrieval={
            "hybrid": True,
            "dense": True,
            "lexical": True,
            "reranking": True,
        },
        filter_semantics=SearchFilterSemantics(
            between_fields="AND",
            within_field_values="OR",
            list_fields=sorted(LIST_SEARCH_FILTERS),
            invalid_filters="rejected",
        ),
        implemented_filters=implemented,
        planned_filters=planned,
        display_only_metadata=display_only,
    )


@router.get("/index-versions", response_model=IndexVersionListResponse)
def list_index_versions(
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0),
) -> IndexVersionListResponse:
    bounded_limit = _bounded_limit(limit)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    name,
                    embedding_provider,
                    embedding_model,
                    embedding_dimension,
                    vector_collection,
                    chunking_version,
                    split_strategy,
                    chunk_size,
                    chunk_overlap,
                    min_chunk_size,
                    max_chunk_size,
                    is_active,
                    created_at,
                    COUNT(*) OVER()::int AS total_count
                FROM index_versions
                ORDER BY created_at DESC, name
                LIMIT %s OFFSET %s
                """,
                (bounded_limit, offset),
            )
            rows = cur.fetchall()
    return IndexVersionListResponse(
        items=[
            IndexVersionRead(**_without_total_count(row))
            for row in rows
        ],
        limit=bounded_limit,
        offset=offset,
        total=_total(rows[0] if rows else None),
    )


@router.get("/index-versions/active", response_model=IndexVersionRead)
def get_active_index_version() -> IndexVersionRead:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    name,
                    embedding_provider,
                    embedding_model,
                    embedding_dimension,
                    vector_collection,
                    chunking_version,
                    split_strategy,
                    chunk_size,
                    chunk_overlap,
                    min_chunk_size,
                    max_chunk_size,
                    is_active,
                    created_at
                FROM index_versions
                WHERE is_active IS TRUE
                ORDER BY created_at DESC
                LIMIT 1
                """,
            )
            row = cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="No active index version found")
    return IndexVersionRead(**row)


@router.post(
    "/index-versions/{index_version_id}/promote",
    response_model=PromoteIndexVersionResponse,
    include_in_schema=False,
)
def promote_index_version(index_version_id: UUID) -> PromoteIndexVersionResponse:
    warnings: list[str] = []
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM index_versions
                WHERE id = %s
                """,
                (index_version_id,),
            )
            index_version = cur.fetchone()
            if index_version is None:
                raise HTTPException(status_code=404, detail="Index version not found")

            cur.execute(
                """
                SELECT
                    COUNT(*)::int AS chunk_count,
                    COUNT(*) FILTER (
                        WHERE COALESCE(metadata->>'source_code', '') = ''
                    )::int AS chunks_without_source_code,
                    COUNT(*) FILTER (
                        WHERE COALESCE(metadata->>'role_documentaire', '') = ''
                    )::int AS chunks_without_role_documentaire,
                    COUNT(*) FILTER (
                        WHERE page_start IS NULL AND page_end IS NULL
                    )::int AS chunks_without_pages
                FROM document_chunks
                WHERE index_version_id = %s
                """,
                (index_version_id,),
            )
            checks = cur.fetchone()
            chunk_count = int(checks["chunk_count"] or 0)
            if chunk_count == 0:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "empty_index_version",
                        "message": "Index version has no chunks",
                    },
                )
            if checks["chunks_without_source_code"]:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "missing_source_code",
                        "message": "Some chunks do not have source_code metadata",
                        "count": checks["chunks_without_source_code"],
                    },
                )
            if checks["chunks_without_role_documentaire"]:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "missing_role_documentaire",
                        "message": "Some chunks do not have role_documentaire metadata",
                        "count": checks["chunks_without_role_documentaire"],
                    },
                )
            if checks["chunks_without_pages"]:
                warnings.append(
                    f"{checks['chunks_without_pages']} chunks have no page_start/page_end"
                )

            qdrant_point_count = _qdrant_point_count(index_version["vector_collection"])
            if qdrant_point_count != chunk_count:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "qdrant_chunk_count_mismatch",
                        "message": "Qdrant point count does not match PostgreSQL chunks",
                        "chunk_count": chunk_count,
                        "qdrant_point_count": qdrant_point_count,
                    },
                )

            cur.execute("UPDATE index_versions SET is_active = false")
            cur.execute(
                """
                UPDATE index_versions
                SET is_active = true
                WHERE id = %s
                """,
                (index_version_id,),
            )

    return PromoteIndexVersionResponse(
        index_version_id=index_version_id,
        is_active=True,
        vector_collection=index_version["vector_collection"],
        chunk_count=chunk_count,
        qdrant_point_count=qdrant_point_count,
        warnings=warnings,
    )


@router.get("/sources", response_model=SourceListResponse)
def list_sources(
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0),
    source_code: str | None = None,
    source_type: str | None = None,
) -> SourceListResponse:
    conditions: list[str] = []
    params: list[Any] = []
    if source_code:
        conditions.append("sources.code = %s")
        params.append(source_code.strip().lower())
    if source_type:
        conditions.append("sources.source_type = %s")
        params.append(source_type.strip().lower())
    where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    bounded_limit = _bounded_limit(limit)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT
                    sources.id AS source_id,
                    sources.code AS source_code,
                    sources.source_type,
                    sources.origin,
                    sources.author,
                    sources.published_at,
                    COUNT(DISTINCT documents.id)::int AS document_count,
                    COUNT(DISTINCT document_chunks.id)::int AS chunk_count,
                    COUNT(*) OVER()::int AS total_count
                FROM sources
                LEFT JOIN documents ON documents.source_id = sources.id
                LEFT JOIN document_chunks
                    ON document_chunks.document_id = documents.id
                {where_sql}
                GROUP BY sources.id
                ORDER BY sources.created_at DESC, sources.code
                LIMIT %s OFFSET %s
                """,
                (*params, bounded_limit, offset),
            )
            rows = cur.fetchall()

    return SourceListResponse(
        items=[_source_from_row(row) for row in rows],
        limit=bounded_limit,
        offset=offset,
        total=_total(rows[0] if rows else None),
    )


def _get_source(*, source_id: UUID | None = None, source_code: str | None = None) -> SourceDetail:
    conditions: list[str] = []
    params: list[Any] = []
    if source_id is not None:
        conditions.append("sources.id = %s")
        params.append(source_id)
    if source_code is not None:
        conditions.append("sources.code = %s")
        params.append(source_code.strip().lower())
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT
                    sources.id AS source_id,
                    sources.code AS source_code,
                    sources.source_type,
                    sources.origin,
                    sources.author,
                    sources.published_at,
                    COUNT(DISTINCT documents.id)::int AS document_count,
                    COUNT(DISTINCT document_chunks.id)::int AS chunk_count
                FROM sources
                LEFT JOIN documents ON documents.source_id = sources.id
                LEFT JOIN document_chunks
                    ON document_chunks.document_id = documents.id
                WHERE {' AND '.join(conditions)}
                GROUP BY sources.id
                """,
                tuple(params),
            )
            row = cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return SourceDetail(**row)


@router.get("/sources/by-code/{source_code}", response_model=SourceDetail)
def get_source_by_code(source_code: str) -> SourceDetail:
    return _get_source(source_code=source_code)


@router.get("/sources/{source_id}", response_model=SourceDetail)
def get_source(source_id: UUID) -> SourceDetail:
    return _get_source(source_id=source_id)


@router.get("/documents", response_model=DocumentListResponse)
def list_documents(
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0),
    source_code: str | None = None,
    role_documentaire: str | None = None,
    theme_tags: list[str] | None = Query(default=None),
    visibility_scope: str | None = None,
    access_level: str | None = None,
) -> DocumentListResponse:
    conditions: list[str] = []
    params: list[Any] = []
    if source_code:
        conditions.append("sources.code = %s")
        params.append(source_code.strip().lower())
    if role_documentaire:
        conditions.append("documents.metadata->>'role_documentaire' = %s")
        params.append(role_documentaire.strip().lower())
    if theme_tags:
        conditions.append("(documents.metadata->'theme_tags') ?| %s")
        params.append([tag.strip() for tag in theme_tags if tag.strip()])
    if visibility_scope:
        conditions.append("documents.metadata->>'visibility_scope' = %s")
        params.append(visibility_scope.strip().lower())
    if access_level:
        conditions.append("documents.metadata->>'access_level' = %s")
        params.append(access_level.strip().lower())
    where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    bounded_limit = _bounded_limit(limit)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT
                    documents.id AS document_id,
                    documents.source_id,
                    sources.code AS source_code,
                    documents.title,
                    documents.filename,
                    documents.mime_type,
                    documents.status::text AS status,
                    documents.created_at,
                    documents.metadata,
                    COUNT(document_chunks.id)::int AS chunk_count,
                    COUNT(*) OVER()::int AS total_count
                FROM documents
                JOIN sources ON sources.id = documents.source_id
                LEFT JOIN document_chunks
                    ON document_chunks.document_id = documents.id
                {where_sql}
                GROUP BY documents.id, sources.code
                ORDER BY documents.created_at DESC, documents.title
                LIMIT %s OFFSET %s
                """,
                (*params, bounded_limit, offset),
            )
            rows = cur.fetchall()

    items = [
        DocumentSummary(
            **{
                **_without_total_count(row),
                "metadata": _safe_metadata(row.get("metadata")),
            },
        )
        for row in rows
    ]
    return DocumentListResponse(
        items=items,
        limit=bounded_limit,
        offset=offset,
        total=_total(rows[0] if rows else None),
    )


@router.get("/documents/{document_id}", response_model=DocumentDetail)
def get_document(document_id: UUID) -> DocumentDetail:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    documents.id AS document_id,
                    documents.source_id,
                    sources.code AS source_code,
                    documents.title,
                    documents.filename,
                    documents.mime_type,
                    documents.status::text AS status,
                    documents.created_at,
                    documents.metadata,
                    COUNT(document_chunks.id)::int AS chunk_count
                FROM documents
                JOIN sources ON sources.id = documents.source_id
                LEFT JOIN document_chunks
                    ON document_chunks.document_id = documents.id
                WHERE documents.id = %s
                GROUP BY documents.id, sources.code
                """,
                (document_id,),
            )
            row = cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentDetail(
        **{
            **row,
            "metadata": _safe_metadata(row.get("metadata")),
        },
    )


@router.get("/documents/{document_id}/chunks", response_model=ChunkListResponse)
def list_document_chunks(
    document_id: UUID,
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0),
    include_content: bool = False,
) -> ChunkListResponse:
    bounded_limit = _bounded_limit(limit)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id AS chunk_id,
                    document_id,
                    index_version_id,
                    chunk_index,
                    page_start,
                    page_end,
                    token_count,
                    content,
                    metadata,
                    COUNT(*) OVER()::int AS total_count
                FROM document_chunks
                WHERE document_id = %s
                ORDER BY chunk_index
                LIMIT %s OFFSET %s
                """,
                (document_id, bounded_limit, offset),
            )
            rows = cur.fetchall()

    items = []
    for row in rows:
        payload = dict(row)
        payload.pop("total_count", None)
        payload["content"] = payload["content"] if include_content else None
        payload["metadata"] = _safe_metadata(payload.get("metadata"))
        items.append(ChunkSummary(**payload))

    return ChunkListResponse(
        items=items,
        limit=bounded_limit,
        offset=offset,
        total=_total(rows[0] if rows else None),
    )


@router.get("/chunks/{chunk_id}", response_model=ChunkDetail)
def get_chunk(
    chunk_id: UUID,
    include_content: bool = True,
) -> ChunkDetail:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id AS chunk_id,
                    document_id,
                    index_version_id,
                    chunk_index,
                    page_start,
                    page_end,
                    token_count,
                    content,
                    metadata
                FROM document_chunks
                WHERE id = %s
                """,
                (chunk_id,),
            )
            row = cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Chunk not found")
    payload = dict(row)
    payload["content"] = payload["content"] if include_content else None
    payload["metadata"] = _safe_metadata(payload.get("metadata"))
    return ChunkDetail(**payload)


@router.get(
    "/documents/{document_id}/extraction",
    response_model=DocumentExtractionRead,
)
def get_document_extraction(
    document_id: UUID,
    page_from: int | None = Query(default=None, ge=1),
    page_to: int | None = Query(default=None, ge=1),
    include_text: bool = True,
) -> DocumentExtractionRead:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, title, metadata
                FROM documents
                WHERE id = %s
                """,
                (document_id,),
            )
            row = cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Document not found")

    metadata = row.get("metadata") or {}
    pages = metadata.get("extracted_pages") or []
    filtered_pages = []
    for page in pages:
        page_number = page.get("page")
        if page_from is not None and page_number < page_from:
            continue
        if page_to is not None and page_number > page_to:
            continue
        page_payload = dict(page)
        if not include_text:
            page_payload["text"] = None
        filtered_pages.append(ExtractedPageRead(**page_payload))

    return DocumentExtractionRead(
        document_id=row["id"],
        title=row["title"],
        extraction=metadata.get("extraction") or {},
        pages=filtered_pages[:MAX_LIMIT],
        page_from=page_from,
        page_to=page_to,
        total_pages=len(pages),
    )


@router.get("/runs/{run_id}", response_model=RunDetail)
def get_run(run_id: UUID) -> RunDetail:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id AS run_id,
                    run_type,
                    status::text AS status,
                    index_version_id,
                    input,
                    output,
                    error,
                    started_at,
                    finished_at
                FROM runs
                WHERE id = %s
                """,
                (run_id,),
            )
            row = cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return RunDetail(
        **{
            **row,
            "input": _safe_trace_payload(row.get("input")),
            "output": _safe_trace_payload(row.get("output")),
        },
    )


@router.get("/runs/{run_id}/retrieval-hits", response_model=RetrievalHitListResponse)
def get_run_retrieval_hits(
    run_id: UUID,
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0),
) -> RetrievalHitListResponse:
    bounded_limit = _bounded_limit(limit)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    retrieval_hits.id AS retrieval_hit_id,
                    retrieval_hits.run_id,
                    retrieval_hits.chunk_id,
                    document_chunks.document_id,
                    retrieval_hits.rank_initial,
                    retrieval_hits.rank_final,
                    retrieval_hits.dense_score,
                    retrieval_hits.lexical_score,
                    retrieval_hits.rerank_score,
                    document_chunks.metadata,
                    COUNT(*) OVER()::int AS total_count
                FROM retrieval_hits
                JOIN document_chunks
                    ON document_chunks.id = retrieval_hits.chunk_id
                WHERE retrieval_hits.run_id = %s
                ORDER BY retrieval_hits.rank_final NULLS LAST,
                         retrieval_hits.rank_initial NULLS LAST
                LIMIT %s OFFSET %s
                """,
                (run_id, bounded_limit, offset),
            )
            rows = cur.fetchall()

    items = [
        RetrievalHitDetail(
            **{
                **_without_total_count(row),
                "metadata": _safe_metadata(row.get("metadata")),
            },
        )
        for row in rows
    ]
    return RetrievalHitListResponse(
        items=items,
        limit=bounded_limit,
        offset=offset,
        total=_total(rows[0] if rows else None),
    )


@router.post("/search", response_model=StableSearchResponse)
async def search_documents(payload: StableSearchRequest) -> StableSearchResponse:
    try:
        legacy_response = await documentary_search_documents(
            DocumentarySearchRequest(
                query=payload.query,
                index_version_id=payload.index_version_id,
                top_k=payload.top_k,
                rerank_top_k=payload.rerank_top_k,
                filters=payload.filters,
            )
        )
    except ValueError as exc:
        message = str(exc)
        if "Index version not found" in message:
            raise HTTPException(status_code=404, detail=message) from exc
        raise HTTPException(status_code=400, detail=message) from exc

    score_rows = _fetch_retrieval_score_rows(legacy_response.run_id)
    filters_applied = (
        payload.filters.active_filters()
        if payload.filters is not None
        else {}
    )
    hits = []
    for hit in legacy_response.hits:
        scores = score_rows.get(hit.chunk_id, {})
        hits.append(
            StableSearchHit(
                chunk_id=hit.chunk_id,
                document_id=hit.document_id,
                rank_initial=scores.get("rank_initial"),
                rank_final=hit.rank,
                score=hit.score,
                dense_score=scores.get("dense_score"),
                lexical_score=scores.get("lexical_score"),
                rerank_score=scores.get("rerank_score"),
                content=hit.content,
                metadata=_safe_metadata(hit.metadata),
            )
        )

    return StableSearchResponse(
        run_id=legacy_response.run_id,
        index_version_id=payload.index_version_id,
        filters_applied=filters_applied,
        hits=hits,
    )
