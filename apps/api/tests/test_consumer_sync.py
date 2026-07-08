from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SYNC_SCRIPT = REPO_ROOT / "scripts" / "sync_core_to_consumer.sh"


def test_consumer_sync_script_exists_and_defaults_to_dry_run():
    script = SYNC_SCRIPT.read_text(encoding="utf-8")

    assert "mode_args=(-ain)" in script
    assert "Pass --apply to copy files" in script
    assert "git ls-files -z" in script
    assert "git fetch" not in script
    assert "git checkout" not in script


def test_consumer_sync_script_excludes_consumer_local_configuration():
    script = SYNC_SCRIPT.read_text(encoding="utf-8")

    assert "--exclude='apps/api/config/local/'" in script
    assert "--exclude='apps/api/config/project.yaml'" in script
    assert "--exclude='apps/api/config/metadata_registry.project.yaml'" in script
    assert "--exclude='.env'" in script
    assert "--include='.env.example'" in script
