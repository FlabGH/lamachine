from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

from app.services.documentary.enrichers import EnricherConfig


API_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROJECT_CONFIG_PATH = API_ROOT / "config" / "project.yaml"
PROJECT_CONFIG_PATH_ENV = "PROJECT_CONFIG_PATH"


class MetadataRegistryConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    core: str
    project: str


class DocumentaryProjectConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metadata_registry: MetadataRegistryConfig
    chunking_strategy: str
    retrieval_presets: str
    retrieval_preset: str
    enrichers: list[EnricherConfig] = Field(default_factory=list)


class ProjectConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: str = Field(min_length=1)
    project_name: str = Field(min_length=1)
    config_version: int = Field(ge=1)
    documentary: DocumentaryProjectConfig


def _resolve_project_config_path() -> Path:
    configured_path = os.getenv(PROJECT_CONFIG_PATH_ENV, "").strip()
    if not configured_path:
        return DEFAULT_PROJECT_CONFIG_PATH

    path = Path(configured_path)
    if path.is_absolute():
        return path
    return API_ROOT / path


def load_project_config(path: Path | None = None) -> ProjectConfig:
    config_path = path or _resolve_project_config_path()
    with config_path.open("r", encoding="utf-8") as stream:
        raw_config: Any = yaml.safe_load(stream)

    if not isinstance(raw_config, dict):
        raise ValueError(f"Project config must be a YAML object: {config_path}")

    return ProjectConfig.model_validate(raw_config)


@lru_cache(maxsize=1)
def get_project_config() -> ProjectConfig:
    return load_project_config()


def project_trace_payload() -> dict[str, str | int]:
    config = get_project_config()
    return {
        "project_id": config.project_id,
        "project_name": config.project_name,
        "config_version": config.config_version,
    }
