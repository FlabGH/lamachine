from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
MANIFEST = REPO_ROOT / "corpus" / "sample" / "manifest.yaml"

REQUIRED_DOCUMENT_KEYS = {
    "file",
    "title",
    "source_code",
    "theme_tags",
}


def test_sample_corpus_manifest_parses_as_yaml():
    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))

    assert isinstance(manifest, dict)
    assert isinstance(manifest["documents"], list)
    assert manifest["documents"]


def test_sample_corpus_manifest_has_expected_document_structure():
    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))

    for document in manifest["documents"]:
        assert REQUIRED_DOCUMENT_KEYS <= set(document)
        assert document["file"]
        assert document["title"]
        assert document["source_code"]
        assert isinstance(document["theme_tags"], list)
        assert all(isinstance(tag, str) and tag for tag in document["theme_tags"])
        assert (MANIFEST.parent / "files" / document["file"]).exists()
