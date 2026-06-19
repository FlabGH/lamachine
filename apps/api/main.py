import os

import httpx
from fastapi import FastAPI

from app.api.config import router as config_router
from app.api.consultation import router as consultation_router
from app.api.documentary import router as documentary_router
from app.api.project import router as project_router
from app.db import get_connection
from app.services.project_config import get_project_config

app = FastAPI(title="LaMachine POC API")
app.state.project_config = get_project_config()

app.include_router(config_router)                   # pour prod via Caddy handle_path
app.include_router(documentary_router)              # pour prod via Caddy handle_path
app.include_router(consultation_router)             # API consultation stable /v1
app.include_router(project_router)                  # configuration projet core
app.include_router(config_router, prefix="/api")  # pour tests directs WSL : localhost:8000/api/...
app.include_router(documentary_router, prefix="/api")  # pour tests directs WSL : localhost:8000/api/...
app.include_router(consultation_router, prefix="/api")  # alias local/prod /api/v1/...
app.include_router(project_router, prefix="/api")  # alias local/prod /api/project/...

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
