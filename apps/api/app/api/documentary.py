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
    raise NotImplementedError


@router.post("/search", response_model=SearchResponse)
async def search_documents(payload: SearchRequest) -> SearchResponse:
    raise NotImplementedError


@router.post("/generate-note", response_model=GenerateNoteResponse)
async def generate_note(payload: GenerateNoteRequest) -> GenerateNoteResponse:
    raise NotImplementedError


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
