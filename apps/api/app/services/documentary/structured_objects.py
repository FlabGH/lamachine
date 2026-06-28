from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from app.db import get_connection
from app.services.documentary.contracts import (
    StructuredObjectInput,
    StructuredObjectPayload,
    StructuredObjectProducer,
    StructuredObjectRecord,
)


def _source_span_payload(payload: StructuredObjectPayload) -> dict[str, Any]:
    return payload.source_span.model_dump(mode="json", exclude_none=True)


def _producer_payload(producer: StructuredObjectProducer) -> dict[str, Any]:
    return producer.model_dump(mode="json", exclude_none=True)


def structured_object_collection_name(vector_collection: str) -> str:
    return f"{vector_collection}_objects"


def build_structured_object_qdrant_payload(
    record: StructuredObjectRecord,
) -> dict[str, Any]:
    return {
        "object_id": str(record.object_id),
        "document_id": str(record.document_id),
        "object_type": record.payload.object_type,
        "title": record.payload.title,
        "source_span": record.payload.source_span.model_dump(
            mode="json",
            exclude_none=True,
        ),
        "source_chunk_ids": [str(chunk_id) for chunk_id in record.source_chunk_ids],
        "metadata": record.payload.metadata,
        "producer": record.producer.model_dump(mode="json", exclude_none=True),
    }


def _row_to_record(row: dict[str, Any]) -> StructuredObjectRecord:
    source_chunk_ids = row.get("source_chunk_ids") or []
    return StructuredObjectRecord(
        object_id=row["id"],
        document_id=row["document_id"],
        payload=StructuredObjectPayload(
            object_type=row["object_type"],
            title=row.get("title"),
            content=row["content"],
            source_span=row.get("source_span") or {},
            metadata=row.get("metadata") or {},
            confidence=row.get("confidence"),
        ),
        producer=StructuredObjectProducer.model_validate(row.get("producer") or {}),
        source_chunk_ids=source_chunk_ids,
        qdrant_point_id=row.get("qdrant_point_id"),
    )


def create_structured_object(
    structured_object: StructuredObjectInput,
) -> StructuredObjectRecord:
    payload = structured_object.payload
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO structured_objects (
                    document_id,
                    object_type,
                    title,
                    content,
                    source_span,
                    metadata,
                    producer,
                    confidence
                )
                VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s)
                RETURNING
                    id,
                    document_id,
                    object_type,
                    title,
                    content,
                    source_span,
                    metadata,
                    producer,
                    confidence,
                    qdrant_point_id
                """,
                (
                    structured_object.document_id,
                    payload.object_type,
                    payload.title,
                    payload.content,
                    json.dumps(_source_span_payload(payload)),
                    json.dumps(payload.metadata),
                    json.dumps(_producer_payload(structured_object.producer)),
                    payload.confidence,
                ),
            )
            row = dict(cur.fetchone())
            for chunk_id in structured_object.source_chunk_ids:
                cur.execute(
                    """
                    INSERT INTO structured_object_chunks (
                        structured_object_id,
                        chunk_id
                    )
                    VALUES (%s, %s)
                    """,
                    (row["id"], chunk_id),
                )
            row["source_chunk_ids"] = list(structured_object.source_chunk_ids)
    return _row_to_record(row)


def list_structured_objects(
    *,
    document_id: UUID | None = None,
    object_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[int, list[StructuredObjectRecord]]:
    conditions: list[str] = []
    params: list[Any] = []
    if document_id is not None:
        conditions.append("structured_objects.document_id = %s")
        params.append(document_id)
    if object_type:
        conditions.append("structured_objects.object_type = %s")
        params.append(object_type.strip().lower())
    where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT
                    structured_objects.id,
                    structured_objects.document_id,
                    structured_objects.object_type,
                    structured_objects.title,
                    structured_objects.content,
                    structured_objects.source_span,
                    structured_objects.metadata,
                    structured_objects.producer,
                    structured_objects.confidence,
                    structured_objects.qdrant_point_id,
                    COALESCE(
                        array_agg(structured_object_chunks.chunk_id)
                            FILTER (WHERE structured_object_chunks.chunk_id IS NOT NULL),
                        ARRAY[]::uuid[]
                    ) AS source_chunk_ids,
                    COUNT(*) OVER()::int AS total_count
                FROM structured_objects
                LEFT JOIN structured_object_chunks
                    ON structured_object_chunks.structured_object_id = structured_objects.id
                {where_sql}
                GROUP BY structured_objects.id
                ORDER BY structured_objects.created_at DESC, structured_objects.id
                LIMIT %s OFFSET %s
                """,
                (*params, limit, offset),
            )
            rows = cur.fetchall()

    total = int(rows[0]["total_count"]) if rows else 0
    return total, [_row_to_record(row) for row in rows]


def get_structured_object(object_id: UUID) -> StructuredObjectRecord | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    structured_objects.id,
                    structured_objects.document_id,
                    structured_objects.object_type,
                    structured_objects.title,
                    structured_objects.content,
                    structured_objects.source_span,
                    structured_objects.metadata,
                    structured_objects.producer,
                    structured_objects.confidence,
                    structured_objects.qdrant_point_id,
                    COALESCE(
                        array_agg(structured_object_chunks.chunk_id)
                            FILTER (WHERE structured_object_chunks.chunk_id IS NOT NULL),
                        ARRAY[]::uuid[]
                    ) AS source_chunk_ids
                FROM structured_objects
                LEFT JOIN structured_object_chunks
                    ON structured_object_chunks.structured_object_id = structured_objects.id
                WHERE structured_objects.id = %s
                GROUP BY structured_objects.id
                """,
                (object_id,),
            )
            row = cur.fetchone()
    return None if row is None else _row_to_record(row)


def get_structured_objects_by_ids(
    object_ids: list[UUID],
) -> dict[UUID, StructuredObjectRecord]:
    if not object_ids:
        return {}

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    structured_objects.id,
                    structured_objects.document_id,
                    structured_objects.object_type,
                    structured_objects.title,
                    structured_objects.content,
                    structured_objects.source_span,
                    structured_objects.metadata,
                    structured_objects.producer,
                    structured_objects.confidence,
                    structured_objects.qdrant_point_id,
                    COALESCE(
                        array_agg(structured_object_chunks.chunk_id)
                            FILTER (WHERE structured_object_chunks.chunk_id IS NOT NULL),
                        ARRAY[]::uuid[]
                    ) AS source_chunk_ids
                FROM structured_objects
                LEFT JOIN structured_object_chunks
                    ON structured_object_chunks.structured_object_id = structured_objects.id
                WHERE structured_objects.id = ANY(%s::uuid[])
                GROUP BY structured_objects.id
                """,
                (object_ids,),
            )
            rows = cur.fetchall()
    return {record.object_id: record for record in map(_row_to_record, rows)}
