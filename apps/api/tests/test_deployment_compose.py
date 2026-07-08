import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
COMPOSE_DIR = REPO_ROOT / "infra" / "compose"
LOCAL_COMPOSE = COMPOSE_DIR / "docker-compose.local.yml"
PROD_COMPOSE = COMPOSE_DIR / "docker-compose.prod.yml"
ROOT_COMPOSE = COMPOSE_DIR / "docker-compose.yml"
REMOTE_DEPLOY_SCRIPT = REPO_ROOT / "scripts" / "remote_deploy.sh"
REQUIRED_SERVICES = {"api", "worker", "frontend", "postgres", "qdrant", "caddy"}


def parse_service_names(compose_path: Path) -> list[str]:
    lines = compose_path.read_text(encoding="utf-8").splitlines()
    services = []
    in_services = False
    base_indent = None

    for line in lines:
        stripped = line.lstrip()
        if not in_services:
            if stripped.startswith("services:"):
                in_services = True
                continue
            continue

        if not stripped or stripped.startswith("#"):
            continue

        indent = len(line) - len(stripped)
        if base_indent is None:
            if stripped.startswith("-"):
                continue
            base_indent = indent

        if indent < base_indent:
            break

        if indent == base_indent and ":" in stripped:
            service_name = stripped.split(":", 1)[0].strip()
            if service_name:
                services.append(service_name)

    return services


def docker_compose_available() -> bool:
    docker = shutil.which("docker")
    if not docker:
        return False

    try:
        subprocess.run(
            [docker, "compose", "version"],
            capture_output=True,
            check=True,
            timeout=10,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


@pytest.mark.parametrize(
    "compose_path",
    [LOCAL_COMPOSE, PROD_COMPOSE, ROOT_COMPOSE],
)
def test_docker_compose_file_exists(compose_path: Path):
    assert compose_path.exists() and compose_path.is_file(), f"Missing compose file: {compose_path}"


@pytest.mark.parametrize(
    "compose_path",
    [LOCAL_COMPOSE, PROD_COMPOSE, ROOT_COMPOSE],
)
def test_docker_compose_defines_required_services(compose_path: Path):
    service_names = parse_service_names(compose_path)
    assert service_names, f"No services parsed from {compose_path}"
    assert REQUIRED_SERVICES.issubset(service_names), (
        f"Expected services {REQUIRED_SERVICES} in {compose_path}, got {service_names}"
    )


@pytest.mark.skipif(
    not docker_compose_available(),
    reason="docker compose unavailable in the current environment",
)
def test_docker_compose_can_render_config():
    compose_file = str(ROOT_COMPOSE)
    docker = shutil.which("docker")
    result = subprocess.run(
        [docker, "compose", "-f", compose_file, "config", "--services"],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )

    rendered_services = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    assert set(REQUIRED_SERVICES).issubset(set(rendered_services)), (
        f"Rendered compose services missing expected items: {rendered_services}"
    )


@pytest.mark.skipif(
    not docker_compose_available(),
    reason="docker compose unavailable in the current environment",
)
def test_root_compose_syntax_is_valid():
    compose_file = str(ROOT_COMPOSE)
    docker = shutil.which("docker")
    subprocess.run(
        [docker, "compose", "-f", compose_file, "config"],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )


def test_remote_deploy_defaults_to_prod_compose_override():
    script = REMOTE_DEPLOY_SCRIPT.read_text(encoding="utf-8")

    assert "REMOTE_DOCKER_COMPOSE_FILES=" in script
    assert "infra/compose/docker-compose.yml infra/compose/docker-compose.prod.yml" in script
    assert 'compose_args+=("-f" "\\$compose_file")' in script
    assert 'docker compose "\\${compose_args[@]}" up -d --build' in script


def test_remote_rebuild_uses_consolidated_schema_file():
    script = REMOTE_DEPLOY_SCRIPT.read_text(encoding="utf-8")

    assert "apps/api/app/db/migrations/000_current_schema.sql" in script
    assert "/tmp/000_current_schema.sql" in script
    assert "apps/api/app/db/migrations/001_documentary_schema.sql" not in script
    assert "apps/api/app/db/migrations/003_structured_objects.sql" not in script


def test_root_compose_defines_project_name_from_environment():
    root_compose = ROOT_COMPOSE.read_text(encoding="utf-8").lstrip()

    assert root_compose.startswith("name: ${COMPOSE_PROJECT_NAME:-lapythie}")


def test_local_compose_ports_are_environment_configurable():
    local_compose = LOCAL_COMPOSE.read_text(encoding="utf-8")
    root_compose = ROOT_COMPOSE.read_text(encoding="utf-8")

    assert "${API_HOST_PORT:-8000}:8000" in local_compose
    assert "${FRONTEND_HOST_PORT:-5173}:5173" in local_compose
    assert "${POSTGRES_HOST_PORT:-55432}:5432" in local_compose
    assert "${QDRANT_HOST_PORT:-6333}:6333" in local_compose
    assert "${CADDY_HTTP_PORT:-80}:80" in root_compose
    assert "${CADDY_HTTPS_PORT:-443}:443" in root_compose
