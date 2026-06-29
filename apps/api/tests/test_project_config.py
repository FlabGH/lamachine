from pathlib import Path

from app.api.project import get_project_config_endpoint
from app.services import project_config
from app.services.project_config import (
    load_project_config,
    project_trace_payload,
)
from main import app


def test_project_config_loads_default_contract():
    config = load_project_config()

    assert config.project_id
    assert config.project_name
    assert config.config_version == 1
    assert config.documentary.metadata_registry.core == (
        "config/metadata_registry.core.yaml"
    )
    assert config.documentary.metadata_registry.project == (
        "config/metadata_registry.project.yaml"
    )
    assert config.documentary.chunking_strategy == "index_version_runtime"
    assert config.documentary.retrieval_presets == "config/retrieval_presets.yaml"
    assert config.documentary.retrieval_preset == "hybrid_dense_lexical_rerank_v1"
    assert config.documentary.enrichers == []


def test_project_config_path_can_be_overridden(monkeypatch, tmp_path):
    config_path = tmp_path / "project.yaml"
    config_path.write_text(
        "\n".join(
            [
                "project_id: corpus-controle",
                "project_name: CorpusControle",
                "config_version: 2",
                "documentary:",
                "  metadata_registry:",
                "    core: config/registry.core.yaml",
                "    project: config/registry.project.yaml",
                "  chunking_strategy: generic_recursive_v1",
                "  retrieval_presets: config/retrieval_presets.yaml",
                "  retrieval_preset: control_hybrid_v1",
                "  enrichers:",
                "    - name: noop_enricher_v1",
                "      enabled: false",
                "      stages: [pre_chunking]",
                "      parameters: {}",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("PROJECT_CONFIG_PATH", str(config_path))
    project_config.get_project_config.cache_clear()

    config = project_config.get_project_config()

    assert config.project_id == "corpus-controle"
    assert config.project_name == "CorpusControle"
    assert config.config_version == 2
    assert config.documentary.retrieval_presets == "config/retrieval_presets.yaml"
    assert config.documentary.retrieval_preset == "control_hybrid_v1"
    assert config.documentary.enrichers[0].name == "noop_enricher_v1"
    assert config.documentary.enrichers[0].enabled is False


def test_project_config_endpoint_returns_loaded_config(monkeypatch):
    monkeypatch.delenv("PROJECT_CONFIG_PATH", raising=False)
    project_config.get_project_config.cache_clear()

    assert get_project_config_endpoint() == project_config.get_project_config()


def test_project_config_api_endpoint_is_exposed(monkeypatch):
    monkeypatch.delenv("PROJECT_CONFIG_PATH", raising=False)
    project_config.get_project_config.cache_clear()

    paths = {route.path for route in app.routes}

    assert "/project/config" in paths
    assert "/api/project/config" in paths
    assert get_project_config_endpoint().model_dump() == (
        project_config.get_project_config().model_dump()
    )


def test_project_trace_payload_contains_identity_only(monkeypatch):
    monkeypatch.delenv("PROJECT_CONFIG_PATH", raising=False)
    project_config.get_project_config.cache_clear()

    config = project_config.get_project_config()
    assert project_trace_payload() == {
        "project_id": config.project_id,
        "project_name": config.project_name,
        "config_version": config.config_version,
    }


def test_project_config_path_relative_to_api_root(monkeypatch):
    monkeypatch.setenv("PROJECT_CONFIG_PATH", "config/project.yaml")
    project_config.get_project_config.cache_clear()

    assert project_config.get_project_config() == load_project_config(
        Path(project_config.API_ROOT) / "config" / "project.yaml"
    )
