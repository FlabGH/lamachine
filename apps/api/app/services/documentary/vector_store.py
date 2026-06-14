from __future__ import annotations

import os
from uuid import UUID

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, Filter, PointStruct, VectorParams


QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")


def get_qdrant_client() -> QdrantClient:
    return QdrantClient(url=QDRANT_URL)


def ensure_collection(
    client: QdrantClient,
    *,
    collection_name: str,
    vector_size: int,
) -> None:
    collections = client.get_collections().collections
    existing = {collection.name for collection in collections}

    if collection_name not in existing:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            ),
        )


def upsert_chunks(
    client: QdrantClient,
    *,
    collection_name: str,
    points: list[tuple[UUID, list[float], dict]],
) -> None:
    client.upsert(
        collection_name=collection_name,
        points=[
            PointStruct(
                id=str(point_id),
                vector=vector,
                payload=payload,
            )
            for point_id, vector, payload in points
        ],
    )

def search_chunks(
    client: QdrantClient,
    *,
    collection_name: str,
    query_vector: list[float],
    limit: int,
    query_filter: Filter | None = None,
):
    result = client.query_points(
        collection_name=collection_name,
        query=query_vector,
        query_filter=query_filter,
        limit=limit,
        with_payload=True,
    )
    return result.points
