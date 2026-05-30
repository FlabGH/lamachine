from pathlib import Path

import yaml

from app.services.documentary.metadata_contract import normalize_document_metadata


REPO_ROOT = Path(__file__).resolve().parents[3]
MANIFEST = REPO_ROOT / "corpus" / "poc_ia" / "manifest.yaml"

REQUIRED_DOCUMENT_KEYS = {
    "file",
    "title",
    "source_code",
    "role_documentaire",
    "famille_politique",
    "positionnement",
    "niveau_confiance",
    "type_document",
    "usage_probatoire",
    "statut_metadonnees",
    "mode_qualification",
    "theme_tags",
}


def test_poc_corpus_manifest_parses_as_yaml():
    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))

    assert isinstance(manifest, dict)
    assert isinstance(manifest["documents"], list)
    assert manifest["documents"]


def test_poc_corpus_manifest_has_expected_document_structure():
    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))

    for document in manifest["documents"]:
        assert REQUIRED_DOCUMENT_KEYS <= set(document)
        assert document["file"]
        assert document["title"]
        assert document["source_code"]
        normalize_document_metadata(document)
