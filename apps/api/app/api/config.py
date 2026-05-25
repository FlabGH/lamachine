from __future__ import annotations

from fastapi import APIRouter

from app.services.frontend_config import build_frontend_config


router = APIRouter(prefix="/config", tags=["config"])


@router.get("/frontend")
def get_frontend_config() -> dict:
    return build_frontend_config()
