from __future__ import annotations

import hashlib
import os
import re
from enum import Enum
from uuid import UUID

import psycopg
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel, Field

import json

from app.db import get_connection
from app.services.documentary.ingestion import (
    extract_pdf_with_optional_ocr,
    normalize_text,
    save_uploaded_file,
    sha256_bytes,
)

from app.services.documentary.chunking import (
    ChunkingConfig,
    chunk_text,
    deduplicate_chunks,
)
from app.services.documentary.metadata_contract import (
    build_chunk_metadata,
    build_qdrant_payload,
    normalize_ingestion_metadata,
)

from app.services.ai.factory import (
    get_embedding_client,
    get_llm_client,
    get_ocr_client,
    get_reranker_client,
)
from app.services.ai.presets import get_ai_backend_preset_name
from app.services.documentary.vector_store import (
    ensure_collection,
    get_qdrant_client,
    upsert_chunks,
)

from app.services.ai.clients import RerankCandidate
from app.services.documentary.vector_store import search_chunks

from app.services.ai.clients import LLMMessage

router = APIRouter(prefix="/documentary", tags=["documentary"])


DENSE_WEIGHT = 0.6
LEXICAL_WEIGHT = 0.4
DEFAULT_SEARCH_TOP_K_ENV = "DOCUMENTARY_SEARCH_TOP_K"
DEFAULT_RERANK_TOP_K_ENV = "DOCUMENTARY_RERANK_TOP_K"
POC_DEFAULT_SEARCH_TOP_K = 30
POC_DEFAULT_RERANK_TOP_K = 20
LEXICAL_SEARCH_CONFIG = "french"
LEXICAL_MAX_QUERY_TERMS = 12
LEXICAL_MIN_TERM_LENGTH = 3
LEXICAL_STOPWORDS = {
    "avec",
    "aux",
    "dans",
    "des",
    "donc",
    "elle",
    "elles",
    "est",
    "etre",
    "être",
    "fait",
    "faut",
    "ils",
    "les",
    "leur",
    "leurs",
    "mais",
    "par",
    "pas",
    "peut",
    "pour",
    "que",
    "quel",
    "quelle",
    "quels",
    "quelles",
    "quoi",
    "sont",
    "sur",
    "une",
    "vers",
}
LEXICAL_SEARCH_TEXT_SQL = """
concat_ws(
    ' ',
    content,
    replace(COALESCE(metadata->>'source_code', ''), '_', ' '),
    replace(COALESCE(metadata->>'document_title', ''), '_', ' '),
    replace(COALESCE(metadata->>'role_documentaire', ''), '_', ' '),
    replace(COALESCE(metadata->>'theme_tags', ''), '_', ' ')
)
"""


def _significant_lexical_terms(query: str) -> list[str]:
    terms: list[str] = []
    seen: set[str] = set()
    for raw_term in re.findall(r"[0-9A-Za-zÀ-ÖØ-öø-ÿ_]+", query.lower()):
        term = raw_term.strip("_'-")
        if len(term) < LEXICAL_MIN_TERM_LENGTH:
            continue
        if term in LEXICAL_STOPWORDS:
            continue
        if term in seen:
            continue
        seen.add(term)
        terms.append(term)
        if len(terms) >= LEXICAL_MAX_QUERY_TERMS:
            break
    return terms


def _build_lexical_websearch_query(query: str) -> str | None:
    terms = _significant_lexical_terms(query)
    if not terms:
        return None
    return " OR ".join(terms)


def _json_trace_hash(payload: dict | list) -> str:
    serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _env_int(name: str, default: int) -> int:
    raw_value = os.getenv(name, "").strip()
    if not raw_value:
        return default
    try:
        value = int(raw_value)
    except ValueError:
        return default
    return value if value > 0 else default


def _default_search_top_k() -> int:
    return _env_int(DEFAULT_SEARCH_TOP_K_ENV, POC_DEFAULT_SEARCH_TOP_K)


def _default_rerank_top_k() -> int:
    return _env_int(DEFAULT_RERANK_TOP_K_ENV, POC_DEFAULT_RERANK_TOP_K)


def _adapter_response_metadata(client, raw: dict | None = None) -> dict:
    metadata = {"adapter": client.__class__.__name__}
    if raw:
        metadata.update(raw)
    return metadata


class RunStatus(str, Enum):
    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


class OutputPersona(str, Enum):
    base = "base"
    elu = "elu"
    porte_parole = "porte_parole"
    militant = "militant"
    presse = "presse"


class SourceCreate(BaseModel):
    code: str
    source_type: str = Field(examples=["pdf", "text"])
    origin: str | None = None
    author: str | None = None


class SourceRead(SourceCreate):
    id: UUID


class DocumentRead(BaseModel):
    id: UUID
    source_id: UUID
    title: str
    mime_type: str
    status: str


class IngestionResponse(BaseModel):
    run_id: UUID
    source_id: UUID
    document_id: UUID
    status: RunStatus


class ExtractedPageRead(BaseModel):
    page: int
    text: str
    char_count: int
    section_title: str | None = None
    extraction_source: str = "pypdf"
    layout_quality: dict = Field(default_factory=dict)


class ExtractionReportRead(BaseModel):
    method: str | None = None
    status: str | None = None
    ocr_used: bool = False
    ocr_provider: str | None = None
    ocr_model: str | None = None
    ocr_trigger_reason: str | None = None
    ocr_pages_processed: int = 0
    page_count: int | None = None
    pages_with_text: int | None = None
    empty_pages: list[int] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    layout_quality_rules_version: str | None = None
    layout_quality_status: str | None = None
    layout_suspect_pages: list[int] = Field(default_factory=list)
    layout_ocr_pages_requested: list[int] = Field(default_factory=list)
    layout_ocr_pages_replaced: list[int] = Field(default_factory=list)
    layout_ocr_pages_kept_original: list[int] = Field(default_factory=list)
    layout_warnings: list[str] = Field(default_factory=list)


class DocumentExtractionRead(BaseModel):
    document_id: UUID
    title: str
    extraction: ExtractionReportRead
    pages: list[ExtractedPageRead]


class IndexRequest(BaseModel):
    document_id: UUID
    index_version_id: UUID


class ChunkingPreviewRequest(BaseModel):
    index_version_id: UUID | None = None
    chunk_size: int | None = None
    chunk_overlap: int | None = None
    split_strategy: str | None = None
    min_chunk_size: int | None = None
    max_chunk_size: int | None = None
    chunking_version: str | None = None


class ChunkingPreviewChunk(BaseModel):
    chunk_index: int
    content: str
    content_hash: str
    page_start: int | None = None
    page_end: int | None = None
    section_title: str | None = None
    token_count: int
    metadata: dict = Field(default_factory=dict)


class ChunkingPreviewResponse(BaseModel):
    document_id: UUID
    document_title: str
    chunking_config: dict
    chunks: list[ChunkingPreviewChunk]


class RunRead(BaseModel):
    id: UUID
    run_type: str
    status: RunStatus


class SearchRequest(BaseModel):
    query: str
    index_version_id: UUID
    top_k: int = Field(default_factory=_default_search_top_k)
    rerank_top_k: int = Field(default_factory=_default_rerank_top_k)


class SearchHit(BaseModel):
    chunk_id: UUID
    document_id: UUID
    rank: int
    score: float | None = None
    content: str
    metadata: dict = Field(default_factory=dict)


class SearchResponse(BaseModel):
    run_id: UUID
    hits: list[SearchHit]


class GenerateNoteRequest(BaseModel):
    query: str
    index_version_id: UUID
    personas: list[OutputPersona] = Field(
        default_factory=lambda: [
            OutputPersona.elu,
            OutputPersona.militant,
            OutputPersona.presse,
        ]
    )
    top_k: int = Field(default_factory=_default_search_top_k)
    rerank_top_k: int = Field(default_factory=_default_rerank_top_k)
    prompt_version: str = "note_riposte_v1"


class OutputRead(BaseModel):
    id: UUID
    output_type: str
    persona: str | None
    title: str
    status: str
    content_markdown: str


class GenerateNoteResponse(BaseModel):
    generation_run_id: UUID
    retrieval_run_id: UUID
    outputs: list[OutputRead]


@router.post("/sources", response_model=SourceRead)
async def create_source(payload: SourceCreate) -> SourceRead:
    raise NotImplementedError


def _chunk_document_metadata(document_metadata: dict | None) -> dict:
    if not document_metadata:
        return {}
    return {
        key: value
        for key, value in document_metadata.items()
        if key not in {"extraction", "extracted_pages"}
    }


def _parse_ingestion_metadata_json(metadata_json: str | None) -> dict:
    if metadata_json is None or not isinstance(metadata_json, str):
        return {}
    if not metadata_json.strip():
        return {}
    try:
        parsed = json.loads(metadata_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_metadata_json",
                "message": str(exc),
            },
        ) from exc
    if not isinstance(parsed, dict):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_metadata_json",
                "message": "metadata_json must be a JSON object",
            },
        )
    return parsed


def _normalize_ingestion_metadata_or_400(
    metadata_json: str | None,
    *,
    title: str,
    source_code: str,
) -> dict:
    parsed = _parse_ingestion_metadata_json(metadata_json)
    try:
        return normalize_ingestion_metadata(
            parsed,
            title=title,
            source_code=source_code,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_metadata",
                "message": str(exc),
            },
        ) from exc


def _chunking_config_from_index_version(index_version: dict) -> ChunkingConfig:
    return ChunkingConfig.from_index_version(index_version)


def _chunking_config_for_preview(
    payload: ChunkingPreviewRequest,
    index_version: dict | None,
) -> ChunkingConfig:
    base = (
        _chunking_config_from_index_version(index_version)
        if index_version
        else ChunkingConfig()
    )
    return ChunkingConfig(
        chunk_size=payload.chunk_size or base.chunk_size,
        chunk_overlap=(
            payload.chunk_overlap
            if payload.chunk_overlap is not None
            else base.chunk_overlap
        ),
        split_strategy=payload.split_strategy or base.split_strategy,
        min_chunk_size=payload.min_chunk_size or base.min_chunk_size,
        max_chunk_size=payload.max_chunk_size or base.max_chunk_size,
        chunking_version=payload.chunking_version or base.chunking_version,
    )



@router.post("/index", response_model=RunRead)
async def index_document(payload: IndexRequest) -> RunRead:
    embedding_client = get_embedding_client()
    ai_backend_preset = get_ai_backend_preset_name()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    documents.id,
                    documents.source_id,
                    documents.title AS document_title,
                    documents.raw_text,
                    documents.metadata AS document_metadata,
                    sources.code AS source_code
                FROM documents
                JOIN sources ON sources.id = documents.source_id
                WHERE documents.id = %s
                """,
                (payload.document_id,),
            )
            document = cur.fetchone()

            if document is None:
                raise ValueError(f"Document not found: {payload.document_id}")

            cur.execute(
                """
                SELECT *
                FROM index_versions
                WHERE id = %s
                """,
                (payload.index_version_id,),
            )
            index_version = cur.fetchone()

            if index_version is None:
                raise ValueError(f"Index version not found: {payload.index_version_id}")

            if index_version["embedding_dimension"] != embedding_client.dimension:
                raise ValueError(
                    "Embedding dimension mismatch: "
                    f"index_version={index_version['embedding_dimension']} "
                    f"client={embedding_client.dimension}"
                )

            raw_text = document["raw_text"] or ""
            chunking_config = _chunking_config_from_index_version(index_version)
            candidate_chunks = chunk_text(raw_text, config=chunking_config)
            chunks = deduplicate_chunks(candidate_chunks)
            chunks_skipped_duplicate = len(candidate_chunks) - len(chunks)

            cur.execute(
                """
                DELETE FROM document_chunks
                WHERE document_id = %s
                  AND index_version_id = %s
                """,
                (payload.document_id, payload.index_version_id),
            )

            cur.execute(
                """
                INSERT INTO runs (run_type, status, index_version_id, input, output)
                VALUES (%s, %s, %s, %s::jsonb, %s::jsonb)
                RETURNING id
                """,
                (
                    "indexing",
                    "running",
                    payload.index_version_id,
                    json.dumps(
                        {
                            "document_id": str(payload.document_id),
                            "index_version_id": str(payload.index_version_id),
                            "ai_backend_preset": ai_backend_preset,
                            "vector_collection": index_version["vector_collection"],
                            "embedding_provider": embedding_client.provider,
                            "embedding_model": embedding_client.model,
                            "embedding_dimension": embedding_client.dimension,
                            "chunking": chunking_config.metadata(),
                        }
                    ),
                    json.dumps({}),
                ),
            )
            run_id = cur.fetchone()["id"]

            embedding_input = {
                "document_id": str(payload.document_id),
                "index_version_id": str(payload.index_version_id),
                "candidate_chunk_count": len(candidate_chunks),
                "unique_chunk_count": len(chunks),
                "content_hashes": [chunk.content_sha256 for chunk in chunks],
            }

            cur.execute(
                """
                INSERT INTO model_calls (
                    run_id,
                    call_type,
                    provider,
                    model,
                    input_hash,
                    parameters,
                    response_metadata
                )
                VALUES (%s, 'embedding', %s, %s, %s, %s::jsonb, %s::jsonb)
                RETURNING id
                """,
                (
                    run_id,
                    embedding_client.provider,
                    embedding_client.model,
                    _json_trace_hash(embedding_input),
                    json.dumps(
                        {
                            "dimension": embedding_client.dimension,
                            "texts_count": len(chunks),
                            "candidate_texts_count": len(candidate_chunks),
                            "skipped_duplicate_texts_count": chunks_skipped_duplicate,
                            "index_version_id": str(payload.index_version_id),
                            "vector_collection": index_version["vector_collection"],
                            "chunking": chunking_config.metadata(),
                        }
                    ),
                    json.dumps(_adapter_response_metadata(embedding_client)),
                ),
            )
            model_call_id = cur.fetchone()["id"]

            inserted_chunks = []

            for chunk in chunks:
                chunk_metadata = build_chunk_metadata(
                    source_id=document["source_id"],
                    document_id=payload.document_id,
                    document_title=document["document_title"],
                    source_code=document["source_code"],
                    content_sha256=chunk.content_sha256,
                    index_version_id=payload.index_version_id,
                    vector_collection=index_version["vector_collection"],
                    page_start=chunk.page_start,
                    page_end=chunk.page_end,
                    extra={
                        **_chunk_document_metadata(document["document_metadata"]),
                        **chunk.metadata,
                        "embedding_provider": embedding_client.provider,
                        "embedding_model": embedding_client.model,
                        "embedding_dimension": embedding_client.dimension,
                        "model_call_id": str(model_call_id),
                    },
                )

                cur.execute(
                    """
                    INSERT INTO document_chunks (
                        document_id,
                        index_version_id,
                        chunk_index,
                        content,
                        content_sha256,
                        page_start,
                        page_end,
                        token_count,
                        metadata
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                    ON CONFLICT (index_version_id, content_sha256) DO NOTHING
                    RETURNING id
                    """,
                    (
                        payload.document_id,
                        payload.index_version_id,
                        chunk.chunk_index,
                        chunk.content,
                        chunk.content_sha256,
                        chunk.page_start,
                        chunk.page_end,
                        chunk.token_count,
                        json.dumps(chunk_metadata),
                    ),
                )
                inserted = cur.fetchone()
                if inserted is None:
                    chunks_skipped_duplicate += 1
                    continue
                inserted_chunks.append((inserted["id"], chunk))

            embedding_result = None
            if inserted_chunks:
                embedding_result = await embedding_client.embed_texts(
                    [chunk.content for _, chunk in inserted_chunks],
                    metadata={
                        "index_version_id": str(payload.index_version_id),
                        "document_id": str(payload.document_id),
                    },
                )

            cur.execute(
                """
                UPDATE model_calls
                SET response_metadata = %s::jsonb,
                    parameters = %s::jsonb
                WHERE id = %s
                """,
                (
                    json.dumps(
                        _adapter_response_metadata(
                            embedding_client,
                            {
                                **(
                                    (embedding_result.raw or {})
                                    if embedding_result
                                    else {}
                                ),
                                "dimension": (
                                    embedding_result.dimension
                                    if embedding_result
                                    else embedding_client.dimension
                                ),
                                "vectors_count": (
                                    len(embedding_result.vectors)
                                    if embedding_result
                                    else 0
                                ),
                            },
                        )
                    ),
                    json.dumps(
                        {
                            "dimension": (
                                embedding_result.dimension
                                if embedding_result
                                else embedding_client.dimension
                            ),
                            "texts_count": len(inserted_chunks),
                            "candidate_texts_count": len(candidate_chunks),
                            "skipped_duplicate_texts_count": chunks_skipped_duplicate,
                            "index_version_id": str(payload.index_version_id),
                            "vector_collection": index_version["vector_collection"],
                            "chunking": chunking_config.metadata(),
                        }
                    ),
                    model_call_id,
                ),
            )

            if embedding_result:
                qdrant = get_qdrant_client()
                ensure_collection(
                    qdrant,
                    collection_name=index_version["vector_collection"],
                    vector_size=embedding_result.dimension,
                )

                points = []
                for (chunk_id, chunk), vector in zip(
                    inserted_chunks,
                    embedding_result.vectors,
                ):
                    chunk_metadata = build_chunk_metadata(
                        source_id=document["source_id"],
                        document_id=payload.document_id,
                        document_title=document["document_title"],
                        source_code=document["source_code"],
                        content_sha256=chunk.content_sha256,
                        index_version_id=payload.index_version_id,
                        vector_collection=index_version["vector_collection"],
                        page_start=chunk.page_start,
                        page_end=chunk.page_end,
                        extra={
                            **_chunk_document_metadata(document["document_metadata"]),
                            **chunk.metadata,
                            "embedding_provider": embedding_client.provider,
                            "embedding_model": embedding_client.model,
                            "embedding_dimension": embedding_result.dimension,
                            "model_call_id": str(model_call_id),
                        },
                    )
                    points.append(
                        (
                            chunk_id,
                            vector,
                            build_qdrant_payload(
                                chunk_id=chunk_id,
                                chunk_metadata=chunk_metadata,
                            ),
                        )
                    )

                    cur.execute(
                        """
                        UPDATE document_chunks
                        SET qdrant_point_id = %s
                        WHERE id = %s
                        """,
                        (chunk_id, chunk_id),
                    )

                upsert_chunks(
                    qdrant,
                    collection_name=index_version["vector_collection"],
                    points=points,
                )

            cur.execute(
                """
                UPDATE documents
                SET status = 'indexed'
                WHERE id = %s
                """,
                (payload.document_id,),
            )

            cur.execute(
                """
                UPDATE runs
                SET status = 'succeeded',
                    output = %s::jsonb,
                    finished_at = now()
                WHERE id = %s
                """,
                (
                    json.dumps(
                        {
                            "chunks_created": len(inserted_chunks),
                            "chunks_inserted": len(inserted_chunks),
                            "chunks_skipped_duplicate": chunks_skipped_duplicate,
                            "unique_chunks_seen": len(chunks),
                            "candidate_chunks_seen": len(candidate_chunks),
                            "ai_backend_preset": ai_backend_preset,
                            "vector_collection": index_version["vector_collection"],
                            "embedding_provider": embedding_client.provider,
                            "embedding_model": embedding_client.model,
                            "embedding_dimension": (
                                embedding_result.dimension
                                if embedding_result
                                else embedding_client.dimension
                            ),
                            "model_call_id": str(model_call_id),
                            "chunking": chunking_config.metadata(),
                        }
                    ),
                    run_id,
                ),
            )

    return RunRead(
        id=run_id,
        run_type="indexing",
        status=RunStatus.succeeded,
    )


@router.post(
    "/documents/{document_id}/chunking/preview",
    response_model=ChunkingPreviewResponse,
)
async def preview_document_chunking(
    document_id: UUID,
    payload: ChunkingPreviewRequest,
) -> ChunkingPreviewResponse:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, title, raw_text
                FROM documents
                WHERE id = %s
                """,
                (document_id,),
            )
            document = cur.fetchone()
            if document is None:
                raise ValueError(f"Document not found: {document_id}")

            index_version = None
            if payload.index_version_id is not None:
                cur.execute(
                    """
                    SELECT *
                    FROM index_versions
                    WHERE id = %s
                    """,
                    (payload.index_version_id,),
                )
                index_version = cur.fetchone()
                if index_version is None:
                    raise ValueError(
                        f"Index version not found: {payload.index_version_id}"
                    )

    chunking_config = _chunking_config_for_preview(payload, index_version)
    chunks = chunk_text(document["raw_text"] or "", config=chunking_config)
    return ChunkingPreviewResponse(
        document_id=document_id,
        document_title=document["title"],
        chunking_config=chunking_config.metadata(),
        chunks=[
            ChunkingPreviewChunk(
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                content_hash=chunk.content_sha256,
                page_start=chunk.page_start,
                page_end=chunk.page_end,
                section_title=chunk.metadata.get("section_title"),
                token_count=chunk.token_count,
                metadata=chunk.metadata,
            )
            for chunk in chunks
        ],
    )


@router.post("/search", response_model=SearchResponse)
async def search_documents(payload: SearchRequest) -> SearchResponse:
    embedding_client = get_embedding_client()
    reranker = get_reranker_client()
    ai_backend_preset = get_ai_backend_preset_name()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM index_versions
                WHERE id = %s
                """,
                (payload.index_version_id,),
            )
            index_version = cur.fetchone()

            if index_version is None:
                raise ValueError(f"Index version not found: {payload.index_version_id}")

            cur.execute(
                """
                INSERT INTO runs (run_type, status, index_version_id, input, output)
                VALUES (%s, %s, %s, %s::jsonb, %s::jsonb)
                RETURNING id
                """,
                (
                    "retrieval",
                    "running",
                    payload.index_version_id,
                    json.dumps(
                        {
                            "query": payload.query,
                            "top_k": payload.top_k,
                            "rerank_top_k": payload.rerank_top_k,
                            "index_version_id": str(payload.index_version_id),
                            "ai_backend_preset": ai_backend_preset,
                            "vector_collection": index_version["vector_collection"],
                            "embedding_provider": embedding_client.provider,
                            "embedding_model": embedding_client.model,
                            "reranker_provider": reranker.provider,
                            "reranker_model": reranker.model,
                            "dense_weight": DENSE_WEIGHT,
                            "lexical_weight": LEXICAL_WEIGHT,
                        }
                    ),
                    json.dumps({}),
                ),
            )
            run_id = cur.fetchone()["id"]

            query_embedding = await embedding_client.embed_texts([payload.query])
            query_vector = query_embedding.vectors[0]

            cur.execute(
                """
                INSERT INTO model_calls (
                    run_id,
                    call_type,
                    provider,
                    model,
                    input_hash,
                    parameters,
                    response_metadata
                )
                VALUES (%s, 'embedding', %s, %s, %s, %s::jsonb, %s::jsonb)
                RETURNING id
                """,
                (
                    run_id,
                    embedding_client.provider,
                    embedding_client.model,
                    _json_trace_hash(
                        {
                            "query": payload.query,
                            "index_version_id": str(payload.index_version_id),
                        }
                    ),
                    json.dumps(
                        {
                            "dimension": query_embedding.dimension,
                            "texts_count": 1,
                            "index_version_id": str(payload.index_version_id),
                            "vector_collection": index_version["vector_collection"],
                        }
                    ),
                    json.dumps(
                        _adapter_response_metadata(
                            embedding_client,
                            {
                                **(query_embedding.raw or {}),
                                "dimension": query_embedding.dimension,
                                "vectors_count": len(query_embedding.vectors),
                            },
                        )
                    ),
                ),
            )
            query_embedding_model_call_id = cur.fetchone()["id"]

            qdrant = get_qdrant_client()
            dense_hits = search_chunks(
                qdrant,
                collection_name=index_version["vector_collection"],
                query_vector=query_vector,
                limit=payload.top_k,
            )

            dense_scores_by_chunk_id = {
                hit.payload["chunk_id"]: float(hit.score)
                for hit in dense_hits
                if hit.payload and "chunk_id" in hit.payload
            }

            lexical_query = _build_lexical_websearch_query(payload.query)
            if lexical_query:
                cur.execute(
                    f"""
                    WITH lexical_query AS (
                        SELECT websearch_to_tsquery(
                            '{LEXICAL_SEARCH_CONFIG}',
                            %s
                        ) AS tsq
                    ),
                    lexical_chunks AS (
                        SELECT
                            id,
                            document_id,
                            content,
                            metadata,
                            {LEXICAL_SEARCH_TEXT_SQL} AS lexical_text
                        FROM document_chunks
                        WHERE index_version_id = %s
                    )
                    SELECT
                        lexical_chunks.id,
                        lexical_chunks.document_id,
                        lexical_chunks.content,
                        lexical_chunks.metadata,
                        ts_rank_cd(
                            to_tsvector(
                                '{LEXICAL_SEARCH_CONFIG}',
                                lexical_chunks.lexical_text
                            ),
                            lexical_query.tsq
                        ) AS lexical_score
                    FROM lexical_chunks
                    CROSS JOIN lexical_query
                    WHERE lexical_query.tsq <> ''::tsquery
                      AND to_tsvector(
                            '{LEXICAL_SEARCH_CONFIG}',
                            lexical_chunks.lexical_text
                          ) @@ lexical_query.tsq
                    ORDER BY lexical_score DESC
                    LIMIT %s
                    """,
                    (
                        lexical_query,
                        payload.index_version_id,
                        payload.top_k,
                    ),
                )
                lexical_hits = cur.fetchall()
            else:
                lexical_hits = []

            candidate_ids = set(dense_scores_by_chunk_id.keys())
            candidate_ids.update(str(row["id"]) for row in lexical_hits)

            if not candidate_ids:
                cur.execute(
                    """
                    UPDATE runs
                    SET status = 'succeeded',
                        output = %s::jsonb,
                        finished_at = now()
                    WHERE id = %s
                    """,
                    (
                        json.dumps(
                            {
                                "hits": 0,
                                "top_k": payload.top_k,
                                "rerank_top_k": payload.rerank_top_k,
                                "ai_backend_preset": ai_backend_preset,
                                "dense_hits": len(dense_hits),
                                "lexical_hits": len(lexical_hits),
                                "lexical_query": lexical_query,
                                "embedding_model_call_id": str(query_embedding_model_call_id),
                                "vector_collection": index_version["vector_collection"],
                                "embedding_provider": embedding_client.provider,
                                "embedding_model": embedding_client.model,
                                "embedding_dimension": query_embedding.dimension,
                            }
                        ),
                        run_id,
                    ),
                )
                return SearchResponse(run_id=run_id, hits=[])

            cur.execute(
                """
                SELECT id, document_id, content, metadata
                FROM document_chunks
                WHERE id = ANY(%s::uuid[])
                """,
                (list(candidate_ids),),
            )
            candidate_rows = cur.fetchall()

            lexical_scores_by_chunk_id = {
                str(row["id"]): float(row["lexical_score"] or 0.0)
                for row in lexical_hits
            }

            max_dense = max(dense_scores_by_chunk_id.values() or [1.0])
            max_lexical = max(lexical_scores_by_chunk_id.values() or [1.0])

            fused = []
            for row in candidate_rows:
                chunk_id = str(row["id"])
                dense_norm = dense_scores_by_chunk_id.get(chunk_id, 0.0) / max_dense
                lexical_norm = lexical_scores_by_chunk_id.get(chunk_id, 0.0) / max_lexical
                fused_score = (DENSE_WEIGHT * dense_norm) + (LEXICAL_WEIGHT * lexical_norm)
                fused.append((row, fused_score, dense_norm, lexical_norm))

            fused.sort(key=lambda item: item[1], reverse=True)
            fused = fused[: payload.rerank_top_k]
            initial_rank_by_chunk_id = {
                str(row["id"]): rank
                for rank, (row, _, _, _) in enumerate(fused, start=1)
            }

            candidates = [
                RerankCandidate(
                    id=str(row["id"]),
                    text=row["content"],
                    metadata=row["metadata"],
                )
                for row, _, _, _ in fused
            ]

            cur.execute(
                """
                INSERT INTO model_calls (
                    run_id,
                    call_type,
                    provider,
                    model,
                    input_hash,
                    parameters,
                    response_metadata
                )
                VALUES (%s, 'reranking', %s, %s, %s, %s::jsonb, %s::jsonb)
                RETURNING id
                """,
                (
                    run_id,
                    reranker.provider,
                    reranker.model,
                    _json_trace_hash(
                        {
                            "query": payload.query,
                            "candidate_ids": [candidate.id for candidate in candidates],
                            "top_k": payload.rerank_top_k,
                        }
                    ),
                    json.dumps(
                        {
                            "top_k": payload.rerank_top_k,
                            "candidates_count": len(candidates),
                        }
                    ),
                    json.dumps(_adapter_response_metadata(reranker)),
                ),
            )
            rerank_model_call_id = cur.fetchone()["id"]

            reranked = await reranker.rerank(
                payload.query,
                candidates,
                top_k=payload.rerank_top_k,
            )
            row_by_id = {str(row["id"]): row for row, _, _, _ in fused}

            final_hits = []
            for item in reranked:
                row = row_by_id[item.id]

                dense_norm = next(
                    dense for candidate_row, _, dense, _ in fused
                    if str(candidate_row["id"]) == item.id
                )
                lexical_norm = next(
                    lexical for candidate_row, _, _, lexical in fused
                    if str(candidate_row["id"]) == item.id
                )

                cur.execute(
                    """
                    INSERT INTO retrieval_hits (
                        run_id,
                        chunk_id,
                        rank_initial,
                        rank_final,
                        dense_score,
                        lexical_score,
                        rerank_score,
                        model_call_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        run_id,
                        item.id,
                        initial_rank_by_chunk_id.get(item.id),
                        item.rank,
                        dense_norm,
                        lexical_norm,
                        item.score,
                        rerank_model_call_id,
                    ),
                )

                final_hits.append(
                    SearchHit(
                        chunk_id=row["id"],
                        document_id=row["document_id"],
                        rank=item.rank,
                        score=item.score,
                        content=row["content"],
                        metadata=row["metadata"] or {},
                    )
                )

            cur.execute(
                """
                UPDATE runs
                SET status = 'succeeded',
                    output = %s::jsonb,
                    finished_at = now()
                WHERE id = %s
                """,
                (
                    json.dumps(
                        {
                            "hits": len(final_hits),
                            "top_k": payload.top_k,
                            "rerank_top_k": payload.rerank_top_k,
                            "ai_backend_preset": ai_backend_preset,
                            "dense_hits": len(dense_hits),
                            "lexical_hits": len(lexical_hits),
                            "lexical_query": lexical_query,
                            "candidates": len(candidates),
                            "embedding_model_call_id": str(query_embedding_model_call_id),
                            "rerank_model_call_id": str(rerank_model_call_id),
                            "vector_collection": index_version["vector_collection"],
                            "embedding_provider": embedding_client.provider,
                            "embedding_model": embedding_client.model,
                            "embedding_dimension": query_embedding.dimension,
                            "reranker_provider": reranker.provider,
                            "reranker_model": reranker.model,
                            "dense_weight": DENSE_WEIGHT,
                            "lexical_weight": LEXICAL_WEIGHT,
                        }
                    ),
                    run_id,
                ),
            )

    return SearchResponse(run_id=run_id, hits=final_hits)


@router.post("/generate-note", response_model=GenerateNoteResponse)
async def generate_note(payload: GenerateNoteRequest) -> GenerateNoteResponse:
    llm = get_llm_client()
    ai_backend_preset = get_ai_backend_preset_name()

    search_response = await search_documents(
        SearchRequest(
            query=payload.query,
            index_version_id=payload.index_version_id,
            top_k=payload.top_k,
            rerank_top_k=payload.rerank_top_k,
        )
    )

    context_blocks = []
    for hit in search_response.hits:
        context_blocks.append(
            f"[chunk:{hit.chunk_id} | rank:{hit.rank}]\n{hit.content}"
        )

    context = "\n\n---\n\n".join(context_blocks)

    messages = [
        LLMMessage(
            role="system",
            content=(
                "Tu génères une note de riposte sourcée. "
                "Tu ne dois utiliser que les extraits fournis."
            ),
        ),
        LLMMessage(
            role="user",
            content=(
                f"Question / angle : {payload.query}\n\n"
                f"Extraits disponibles :\n\n{context}"
            ),
        ),
    ]

    llm_result = await llm.generate(
        messages,
        temperature=0.2,
        metadata={
            "retrieval_run_id": str(search_response.run_id),
            "prompt_version": payload.prompt_version,
        },
    )
    llm_input = {
        "messages": [
            {"role": message.role, "content": message.content}
            for message in messages
        ],
        "temperature": 0.2,
        "prompt_version": payload.prompt_version,
        "retrieval_run_id": str(search_response.run_id),
        "ai_backend_preset": ai_backend_preset,
    }

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO runs (
                    run_type,
                    status,
                    index_version_id,
                    input,
                    output,
                    finished_at
                )
                VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, now())
                RETURNING id
                """,
                (
                    "generation",
                    "succeeded",
                    payload.index_version_id,
                    json.dumps(
                        {
                            "query": payload.query,
                            "personas": [p.value for p in payload.personas],
                            "retrieval_run_id": str(search_response.run_id),
                            "prompt_version": payload.prompt_version,
                            "ai_backend_preset": ai_backend_preset,
                            "llm_provider": llm.provider,
                            "llm_model": llm.model,
                            "hits_used": len(search_response.hits),
                        }
                    ),
                    json.dumps(
                        {
                            "outputs": len(payload.personas),
                            "retrieval_run_id": str(search_response.run_id),
                            "prompt_version": payload.prompt_version,
                            "ai_backend_preset": ai_backend_preset,
                            "llm_provider": llm.provider,
                            "llm_model": llm.model,
                            "hits_used": len(search_response.hits),
                        }
                    ),
                ),
            )
            generation_run_id = cur.fetchone()["id"]

            cur.execute(
                """
                INSERT INTO model_calls (
                    run_id,
                    call_type,
                    provider,
                    model,
                    prompt_version,
                    input_hash,
                    parameters,
                    response_metadata
                )
                VALUES (%s, 'llm', %s, %s, %s, %s, %s::jsonb, %s::jsonb)
                RETURNING id
                """,
                (
                    generation_run_id,
                    llm.provider,
                    llm.model,
                    payload.prompt_version,
                    _json_trace_hash(llm_input),
                    json.dumps(
                        {
                            "temperature": 0.2,
                            "messages_count": len(messages),
                            "context_hits": len(search_response.hits),
                            "retrieval_run_id": str(search_response.run_id),
                        }
                    ),
                    json.dumps(_adapter_response_metadata(llm, llm_result.raw or {})),
                ),
            )
            llm_model_call_id = cur.fetchone()["id"]

            outputs = []

            for persona in payload.personas:
                content = (
                    f"{llm_result.text}\n\n"
                    f"## Persona\n\n"
                    f"Déclinaison : `{persona.value}`.\n"
                )

                cur.execute(
                    """
                    INSERT INTO outputs (
                        generation_run_id,
                        title,
                        output_type,
                        persona,
                        status,
                        content_markdown,
                        prompt_version,
                        llm_model_call_id,
                        metadata
                    )
                    VALUES (%s, %s, %s, %s, 'draft', %s, %s, %s, %s::jsonb)
                    RETURNING id
                    """,
                    (
                        generation_run_id,
                        f"Note de riposte — {payload.query}",
                        "note_riposte",
                        persona.value,
                        content,
                        payload.prompt_version,
                        llm_model_call_id,
                        json.dumps(
                            {
                                "retrieval_run_id": str(search_response.run_id),
                                "index_version_id": str(payload.index_version_id),
                                "prompt_version": payload.prompt_version,
                                "ai_backend_preset": ai_backend_preset,
                                "llm_provider": llm.provider,
                                "llm_model": llm.model,
                                "llm_model_call_id": str(llm_model_call_id),
                            }
                        ),
                    ),
                )
                output_id = cur.fetchone()["id"]

                for hit in search_response.hits:
                    cur.execute(
                        """
                        SELECT id
                        FROM retrieval_hits
                        WHERE run_id = %s
                          AND chunk_id = %s
                        LIMIT 1
                        """,
                        (search_response.run_id, hit.chunk_id),
                    )
                    retrieval_hit = cur.fetchone()

                    cur.execute(
                        """
                        INSERT INTO output_sources (
                            output_id,
                            chunk_id,
                            retrieval_hit_id,
                            claim,
                            quote
                        )
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            output_id,
                            hit.chunk_id,
                            retrieval_hit["id"] if retrieval_hit else None,
                            payload.query,
                            hit.content[:500],
                        ),
                    )

                outputs.append(
                    OutputRead(
                        id=output_id,
                        output_type="note_riposte",
                        persona=persona.value,
                        title=f"Note de riposte — {payload.query}",
                        status="draft",
                        content_markdown=content,
                    )
                )

    return GenerateNoteResponse(
        generation_run_id=generation_run_id,
        retrieval_run_id=search_response.run_id,
        outputs=outputs,
    )


@router.post("/documents/pdf", response_model=IngestionResponse)
async def ingest_pdf(
    file: UploadFile = File(...),
    source_code: str = Form(...),
    origin: str | None = Form(default=None),
    author: str | None = Form(default=None),
    metadata_json: str | None = Form(default=None),
) -> IngestionResponse:
    title = file.filename or source_code
    normalized_source_code = source_code.strip().lower()
    functional_metadata = _normalize_ingestion_metadata_or_400(
        metadata_json,
        title=title,
        source_code=normalized_source_code,
    )
    content = await file.read()
    storage_path, digest = save_uploaded_file(file.filename or "upload.pdf", content)
    extraction = await extract_pdf_with_optional_ocr(
        storage_path,
        ocr_client=get_ocr_client(),
    )
    raw_text = extraction.raw_text
    document_metadata = {
        **functional_metadata,
        **extraction.metadata(),
    }

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sources (code, source_type, origin, author)
                VALUES (%s, 'pdf', %s, %s)
                RETURNING id
                """,
                (normalized_source_code, origin, author),
            )
            source_id = cur.fetchone()["id"]

            try:
                cur.execute(
                    """
                    INSERT INTO documents (
                        source_id, title, filename, mime_type,
                        storage_path, sha256, status, raw_text, metadata
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, 'parsed', %s, %s::jsonb)
                    RETURNING id
                    """,
                    (
                        source_id,
                        title,
                        file.filename,
                        file.content_type or "application/pdf",
                        storage_path,
                        digest,
                        raw_text,
                        json.dumps(document_metadata),
                    ),
                )
            except psycopg.errors.UniqueViolation as exc:
                if exc.diag.constraint_name != "documents_sha256_key":
                    raise
                raise HTTPException(
                    status_code=409,
                    detail={
                        "error": "document_already_exists",
                        "sha256": digest,
                    },
                ) from exc
            document_id = cur.fetchone()["id"]

            cur.execute(
                """
                INSERT INTO runs (run_type, status, input, output, finished_at)
                VALUES (%s, %s, %s::jsonb, %s::jsonb, now())
                RETURNING id
                """,
                (
                    "ingestion",
                    "succeeded",
                    json.dumps(
                        {
                            "filename": file.filename,
                            "source_code": normalized_source_code,
                            "extraction_status": extraction.status,
                            "metadata": functional_metadata,
                        }
                    ),
                    json.dumps(
                        {
                            "document_id": str(document_id),
                            "extraction": document_metadata["extraction"],
                        }
                    ),
                ),
            )
            run_id = cur.fetchone()["id"]

    return IngestionResponse(
        run_id=run_id,
        source_id=source_id,
        document_id=document_id,
        status=RunStatus.succeeded,
    )


@router.get("/documents/{document_id}/extraction", response_model=DocumentExtractionRead)
async def get_document_extraction(document_id: UUID) -> DocumentExtractionRead:
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
            document = cur.fetchone()

    if document is None:
        raise ValueError(f"Document not found: {document_id}")

    metadata = document["metadata"] or {}
    extraction = metadata.get("extraction") or {}
    pages = metadata.get("extracted_pages") or []

    return DocumentExtractionRead(
        document_id=document["id"],
        title=document["title"],
        extraction=ExtractionReportRead(**extraction),
        pages=[ExtractedPageRead(**page) for page in pages],
    )


@router.post("/documents/text", response_model=IngestionResponse)
async def ingest_text(
    title: str = Form(...),
    text: str = Form(...),
    source_code: str = Form(...),
    origin: str | None = Form(default=None),
    author: str | None = Form(default=None),
    metadata_json: str | None = Form(default=None),
) -> IngestionResponse:
    raw_text = normalize_text(text)
    digest = sha256_bytes(raw_text.encode("utf-8"))
    normalized_source_code = source_code.strip().lower()
    document_metadata = _normalize_ingestion_metadata_or_400(
        metadata_json,
        title=title,
        source_code=normalized_source_code,
    )

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sources (code, source_type, origin, author)
                VALUES (%s, 'text', %s, %s)
                RETURNING id
                """,
                (normalized_source_code, origin, author),
            )
            source_id = cur.fetchone()["id"]

            cur.execute(
                """
                INSERT INTO documents (
                    source_id, title, filename, mime_type,
                    storage_path, sha256, status, raw_text, metadata
                )
                VALUES (%s, %s, NULL, 'text/plain', NULL, %s, 'parsed', %s, %s::jsonb)
                RETURNING id
                """,
                (
                    source_id,
                    title,
                    digest,
                    raw_text,
                    json.dumps(document_metadata),
                ),
            )
            document_id = cur.fetchone()["id"]

            cur.execute(
                """
                INSERT INTO runs (run_type, status, input, output, finished_at)
                VALUES (%s, %s, %s::jsonb, %s::jsonb, now())
                RETURNING id
                """,
                (
                    "ingestion",
                    "succeeded",
                    json.dumps(
                        {
                            "title": title,
                            "source_code": normalized_source_code,
                            "metadata": document_metadata,
                        }
                    ),
                    json.dumps({"document_id": str(document_id)}),
                ),
            )
            run_id = cur.fetchone()["id"]

    return IngestionResponse(
        run_id=run_id,
        source_id=source_id,
        document_id=document_id,
        status=RunStatus.succeeded,
    )
