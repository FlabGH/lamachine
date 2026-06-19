from __future__ import annotations

from fastapi import APIRouter

from app.services.project_config import ProjectConfig, get_project_config


router = APIRouter(prefix="/project", tags=["project"])


@router.get("/config", response_model=ProjectConfig)
def get_project_config_endpoint() -> ProjectConfig:
    return get_project_config()
