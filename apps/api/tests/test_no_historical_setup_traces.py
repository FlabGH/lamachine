from pathlib import Path
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[3]
SKIPPED_DIRS = {
    ".git",
    ".venv",
    ".pytest_cache",
    ".ruff_cache",
    "artifacts",
    "doc",
    "node_modules",
}
SKIPPED_FILES = {
    ".env",
    ".env.lamachine.example",
    ".gitignore",
    "AGENTS.md",
    "SESSION.md",
    Path(__file__).name,
}
SKIPPED_PROJECT_FILES = {
    Path("apps/api/config/project.lamachine.yaml"),
    Path("apps/api/config/metadata_registry.lamachine.yaml"),
    Path("apps/api/tests/test_lamachine_project_config.py"),
    Path("infra/compose/docker-compose.lamachine.yml"),
    Path("scripts/remote_deploy.sh"),
}
FORBIDDEN_MARKERS = (
    "La" + "Machine",
    "la" + "machine",
    "P" + "OC",
    "poc" + "_ia",
    "poc" + "-",
    "phase" + "3",
    "role" + "_documentaire",
    "document" + "_title",
    "note" + "_riposte",
    "/" + "documentary",
)


def _iter_text_files():
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(REPO_ROOT)
        if any(part in SKIPPED_DIRS for part in relative.parts):
            continue
        if relative.name in SKIPPED_FILES:
            continue
        if relative in SKIPPED_PROJECT_FILES:
            continue
        if _is_git_ignored(relative):
            continue
        if path.suffix.lower() in {".pdf", ".png", ".jpg", ".jpeg", ".gif"}:
            continue
        yield path


def _is_git_ignored(relative: Path) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "--quiet", str(relative)],
        cwd=REPO_ROOT,
        check=False,
    )
    return result.returncode == 0


def test_no_historical_setup_markers_remain_in_code_or_config():
    findings = []
    for path in _iter_text_files():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for marker in FORBIDDEN_MARKERS:
            if marker in text:
                findings.append(f"{path.relative_to(REPO_ROOT)}: {marker}")

    assert findings == []
