from __future__ import annotations

from enum import Enum
from uuid import UUID

from fastapi import APIRouter, UploadFile, File, Form
from pydantic import BaseModel, Field

import json

from app.db import get_connection
from app.services.documentary.ingestion import (
    extract_pdf_text,
    normalize_text,
    save_uploaded_file,
    sha256_bytes,
)

from app.services.documentary.chunking import chunk_text

from app.services.ai.factory import get_embedding_client, get_reranker_client, get_llm_client
from app.services.documentary.vector_store import (
    ensure_collection,
    get_qdrant_client,
    upsert_chunks,
)

from app.services.ai.clients import RerankCandidate
from app.services.documentary.vector_store import search_chunks

from app.services.ai.clients import LLMMessage

router = APIRouter(prefix="/documentary", tags=["documentary"])


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
    name: str
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


class IndexRequest(BaseModel):
    document_id: UUID
    index_version_id: UUID


class RunRead(BaseModel):
    id: UUID
    run_type: str
    status: RunStatus


class SearchRequest(BaseModel):
    query: str
    index_version_id: UUID
    top_k: int = 10
    rerank_top_k: int = 5


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
    top_k: int = 10
    rerank_top_k: int = 5
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



@router.post("/index", response_model=RunRead)
async def index_document(payload: IndexRequest) -> RunRead:
    embedding_client = get_embedding_client()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, raw_text
                FROM documents
                WHERE id = %s
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
            chunks = chunk_text(
                raw_text,
                chunk_size_words=index_version["chunk_size"],
                chunk_overlap_words=index_version["chunk_overlap"],
            )

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
                    json.dumps({"document_id": str(payload.document_id)}),
                    json.dumps({}),
                ),
            )
            run_id = cur.fetchone()["id"]

            cur.execute(
                """
                INSERT INTO model_calls (
                    run_id,
                    call_type,
                    provider,
                    model,
                    parameters,
                    response_metadata
                )
                VALUES (%s, 'embedding', %s, %s, %s::jsonb, %s::jsonb)
                RETURNING id
                """,
                (
                    run_id,
                    embedding_client.provider,
                    embedding_client.model,
                    json.dumps({"dimension": embedding_client.dimension}),
                    json.dumps({"adapter": "HashEmbeddingClient"}),
                ),
            )
            model_call_id = cur.fetchone()["id"]

            inserted_chunks = []

            for chunk in chunks:
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
                        json.dumps(
                            {
                                **chunk.metadata,
                                "embedding_provider": embedding_client.provider,
                                "embedding_model": embedding_client.model,
                                "embedding_dimension": embedding_client.dimension,
                                "model_call_id": str(model_call_id),
                                "vector_collection": index_version["vector_collection"],
                            }
                        ),
                    ),
                )
                inserted_chunks.append((cur.fetchone()["id"], chunk))

            embedding_result = await embedding_client.embed_texts(
                [chunk.content for _, chunk in inserted_chunks],
                metadata={
                    "index_version_id": str(payload.index_version_id),
                    "document_id": str(payload.document_id),
                },
            )

            qdrant = get_qdrant_client()
            ensure_collection(
                qdrant,
                collection_name=index_version["vector_collection"],
                vector_size=embedding_result.dimension,
            )

            points = []
            for (chunk_id, chunk), vector in zip(inserted_chunks, embedding_result.vectors):
                points.append(
                    (
                        chunk_id,
                        vector,
                        {
                            "chunk_id": str(chunk_id),
                            "document_id": str(payload.document_id),
                            "index_version_id": str(payload.index_version_id),
                            "content_sha256": chunk.content_sha256,
                            "page_start": chunk.page_start,
                            "page_end": chunk.page_end,
                        },
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
                            "chunks_created": len(chunks),
                            "vector_collection": index_version["vector_collection"],
                            "embedding_provider": embedding_client.provider,
                            "embedding_model": embedding_client.model,
                            "embedding_dimension": embedding_client.dimension,
                            "model_call_id": str(model_call_id),
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

@router.post("/search", response_model=SearchResponse)
async def search_documents(payload: SearchRequest) -> SearchResponse:
    embedding_client = get_embedding_client()
    reranker = get_reranker_client()

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

            query_embedding = await embedding_client.embed_texts([payload.query])
            query_vector = query_embedding.vectors[0]

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

            cur.execute(
                """
                SELECT
                    id,
                    document_id,
                    content,
                    metadata,
                    ts_rank_cd(
                        to_tsvector('simple', content),
                        plainto_tsquery('simple', %s)
                    ) AS lexical_score
                FROM document_chunks
                WHERE index_version_id = %s
                  AND to_tsvector('simple', content)
                      @@ plainto_tsquery('simple', %s)
                ORDER BY lexical_score DESC
                LIMIT %s
                """,
                (
                    payload.query,
                    payload.index_version_id,
                    payload.query,
                    payload.top_k,
                ),
            )
            lexical_hits = cur.fetchall()

            candidate_ids = set(dense_scores_by_chunk_id.keys())
            candidate_ids.update(str(row["id"]) for row in lexical_hits)

            if not candidate_ids:
                cur.execute(
                    """
                    INSERT INTO runs (run_type, status, index_version_id, input, output, finished_at)
                    VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, now())
                    RETURNING id
                    """,
                    (
                        "retrieval",
                        "succeeded",
                        payload.index_version_id,
                        json.dumps({"query": payload.query}),
                        json.dumps({"hits": 0}),
                    ),
                )
                run_id = cur.fetchone()["id"]
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
                fused_score = (0.6 * dense_norm) + (0.4 * lexical_norm)
                fused.append((row, fused_score, dense_norm, lexical_norm))

            fused.sort(key=lambda item: item[1], reverse=True)
            fused = fused[: payload.rerank_top_k]

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
                        }
                    ),
                    json.dumps({}),
                ),
            )
            run_id = cur.fetchone()["id"]

            cur.execute(
                """
                INSERT INTO model_calls (
                    run_id,
                    call_type,
                    provider,
                    model,
                    parameters,
                    response_metadata
                )
                VALUES (%s, 'reranking', %s, %s, %s::jsonb, %s::jsonb)
                RETURNING id
                """,
                (
                    run_id,
                    reranker.provider,
                    reranker.model,
                    json.dumps({"top_k": payload.rerank_top_k}),
                    json.dumps({"adapter": "LexicalOverlapReranker"}),
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
                        None,
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
                    json.dumps({"hits": len(final_hits)}),
                    run_id,
                ),
            )

    return SearchResponse(run_id=run_id, hits=final_hits)


@router.post("/generate-note", response_model=GenerateNoteResponse)
async def generate_note(payload: GenerateNoteRequest) -> GenerateNoteResponse:
    llm = get_llm_client()

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
                        }
                    ),
                    json.dumps({"outputs": len(payload.personas)}),
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
                    parameters,
                    response_metadata
                )
                VALUES (%s, 'llm', %s, %s, %s, %s::jsonb, %s::jsonb)
                RETURNING id
                """,
                (
                    generation_run_id,
                    llm.provider,
                    llm.model,
                    payload.prompt_version,
                    json.dumps({"temperature": 0.2}),
                    json.dumps(llm_result.raw or {}),
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
    source_name: str = Form(...),
    origin: str | None = Form(default=None),
    author: str | None = Form(default=None),
) -> IngestionResponse:
    content = await file.read()
    storage_path, digest = save_uploaded_file(file.filename or "upload.pdf", content)
    raw_text = extract_pdf_text(storage_path)
    title = file.filename or source_name

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sources (name, source_type, origin, author)
                VALUES (%s, 'pdf', %s, %s)
                RETURNING id
                """,
                (source_name, origin, author),
            )
            source_id = cur.fetchone()["id"]

            cur.execute(
                """
                INSERT INTO documents (
                    source_id, title, filename, mime_type,
                    storage_path, sha256, status, raw_text
                )
                VALUES (%s, %s, %s, %s, %s, %s, 'parsed', %s)
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
                    json.dumps({"filename": file.filename, "source_name": source_name}),
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


@router.post("/documents/text", response_model=IngestionResponse)
async def ingest_text(
    title: str = Form(...),
    text: str = Form(...),
    source_name: str = Form(...),
    origin: str | None = Form(default=None),
    author: str | None = Form(default=None),
) -> IngestionResponse:
    raw_text = normalize_text(text)
    digest = sha256_bytes(raw_text.encode("utf-8"))

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sources (name, source_type, origin, author)
                VALUES (%s, 'text', %s, %s)
                RETURNING id
                """,
                (source_name, origin, author),
            )
            source_id = cur.fetchone()["id"]

            cur.execute(
                """
                INSERT INTO documents (
                    source_id, title, filename, mime_type,
                    storage_path, sha256, status, raw_text
                )
                VALUES (%s, %s, NULL, 'text/plain', NULL, %s, 'parsed', %s)
                RETURNING id
                """,
                (source_id, title, digest, raw_text),
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
                    json.dumps({"title": title, "source_name": source_name}),
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
