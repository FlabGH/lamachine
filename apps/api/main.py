import os

import httpx
import psycopg
from fastapi import FastAPI

app = FastAPI(title="LaMachine POC API")

from app.api.documentary import router as documentary_router

app.include_router(documentary_router, prefix="/api")

DATABASE_URL = os.getenv("DATABASE_URL", "")
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "api"}


@app.get("/health/db")
def health_db() -> dict[str, str]:
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("select 1")
            value = cur.fetchone()[0]
    return {"status": "ok", "db": str(value)}


@app.get("/health/qdrant")
async def health_qdrant() -> dict:
    async with httpx.AsyncClient(timeout=5) as client:
        response = await client.get(QDRANT_URL)
        response.raise_for_status()
        return {"status": "ok", "qdrant": response.json()}