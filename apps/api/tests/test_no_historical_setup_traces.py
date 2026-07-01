from pathlib import Path


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
    "AGENTS.md",
    "SESSION.md",
    Path(__file__).name,
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
        if path.suffix.lower() in {".pdf", ".png", ".jpg", ".jpeg", ".gif"}:
            continue
        yield path


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
