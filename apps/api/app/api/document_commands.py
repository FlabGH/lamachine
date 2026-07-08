from __future__ import annotations

from fastapi import APIRouter

from app.api.documentary import (
    ChunkingPreviewResponse,
    IngestionResponse,
    RunRead,
    index_document,
    ingest_pdf,
    ingest_text,
    preview_document_chunking,
)


router = APIRouter(tags=["document-commands"])

router.add_api_route(
    "/documents/pdf",
    ingest_pdf,
    methods=["POST"],
    response_model=IngestionResponse,
)
router.add_api_route(
    "/documents/text",
    ingest_text,
    methods=["POST"],
    response_model=IngestionResponse,
)
router.add_api_route(
    "/index",
    index_document,
    methods=["POST"],
    response_model=RunRead,
)
router.add_api_route(
    "/documents/{document_id}/chunking/preview",
    preview_document_chunking,
    methods=["POST"],
    response_model=ChunkingPreviewResponse,
)
