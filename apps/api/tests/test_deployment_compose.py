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


def test_compose_files_do_not_define_project_name():
    root_compose = ROOT_COMPOSE.read_text(encoding="utf-8").lstrip()
    local_compose = LOCAL_COMPOSE.read_text(encoding="utf-8").lstrip()
    prod_compose = PROD_COMPOSE.read_text(encoding="utf-8").lstrip()

    assert not root_compose.startswith("name:")
    assert not local_compose.startswith("name:")
    assert not prod_compose.startswith("name:")
