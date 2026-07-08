import os

import httpx
from fastapi import FastAPI

from app.api.consultation import router as consultation_router
from app.api.project import router as project_router
from app.db import get_connection
from app.services.documentary.metadata_registry import get_metadata_registry
from app.services.project_config import get_project_config

app = FastAPI(title="LaPythie API")
app.state.project_config = get_project_config()
app.state.metadata_registry = get_metadata_registry()

app.include_router(consultation_router, prefix="/api")
app.include_router(project_router, prefix="/api")

QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "api"}


@app.get("/health/db")
def health_db() -> dict[str, str]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("select 1 as health_check")
            value = cur.fetchone()["health_check"]
    return {"status": "ok", "db": str(value)}


@app.get("/health/qdrant")
async def health_qdrant() -> dict:
    async with httpx.AsyncClient(timeout=5) as client:
        response = await client.get(QDRANT_URL)
        response.raise_for_status()
        return {"status": "ok", "qdrant": response.json()}
