from uuid import UUID

import pytest

from app.services.documentary.metadata_contract import (
    build_chunk_metadata,
    build_qdrant_payload,
    missing_chunk_metadata_keys,
    normalize_document_metadata,
    validate_chunk_metadata,
)


SOURCE_ID = UUID("00000000-0000-0000-0000-000000000001")
DOCUMENT_ID = UUID("00000000-0000-0000-0000-000000000002")
INDEX_VERSION_ID = UUID("00000000-0000-0000-0000-000000000003")


def _document_metadata(**overrides):
    data = {
        "title": "Programme RN IA",
        "source_code": " RN ",
        "role_documentaire": "opposition",
        "famille_politique": "extreme_droite",
        "positionnement": "adversaire",
        "niveau_confiance": "eleve",
        "type_document": "programme_politique",
        "usage_probatoire": "position_officielle",
        "statut_metadonnees": "valide_humain",
        "mode_qualification": "manuel",
        "qualification_confidence": 0.9,
        "qualification_rationale": "Source primaire explicitement positionnée.",
        "validated_by": "redaction",
        "validated_at": "2026-05-30T00:00:00Z",
        "theme_tags": [" ia ", "travail", ""],
    }
    data.update(overrides)
    return data


def _metadata(**overrides):
    data = {
        "source_id": SOURCE_ID,
        "document_id": DOCUMENT_ID,
        "document_title": "Document fictif",
        "source_code": "source_fictive",
        "content_sha256": "abc123",
        "index_version_id": INDEX_VERSION_ID,
        "vector_collection": "test_collection",
        "page_start": 1,
        "page_end": 2,
        "extra": {"chunking_strategy": "word_window_v1"},
    }
    data.update(overrides)
    return build_chunk_metadata(**data)


def test_build_chunk_metadata_serializes_ids_and_keeps_pages():
    metadata = _metadata()

    assert metadata["source_id"] == str(SOURCE_ID)
    assert metadata["document_id"] == str(DOCUMENT_ID)
    assert metadata["index_version_id"] == str(INDEX_VERSION_ID)
    assert metadata["document_title"] == "Document fictif"
    assert metadata["source_code"] == "source_fictive"
    assert metadata["page_start"] == 1
    assert metadata["page_end"] == 2
    assert metadata["chunking_strategy"] == "word_window_v1"


def test_build_chunk_metadata_adds_body_section_when_no_page_is_available():
    metadata = _metadata(page_start=None, page_end=None)

    assert metadata["section"] == "body"
    assert "page_start" not in metadata
    assert "page_end" not in metadata
    validate_chunk_metadata(metadata)


def test_build_chunk_metadata_keeps_explicit_section_without_pages():
    metadata = _metadata(page_start=None, page_end=None, section="introduction")

    assert metadata["section"] == "introduction"
    validate_chunk_metadata(metadata)


def test_missing_chunk_metadata_keys_detects_critical_missing_values():
    metadata = _metadata()
    del metadata["source_code"]
    metadata["vector_collection"] = ""

    assert missing_chunk_metadata_keys(metadata) == ["source_code", "vector_collection"]


def test_missing_chunk_metadata_keys_requires_page_or_section():
    metadata = _metadata()
    del metadata["page_start"]
    del metadata["page_end"]

    assert missing_chunk_metadata_keys(metadata) == ["page_or_section"]


def test_validate_chunk_metadata_raises_for_incomplete_metadata():
    metadata = _metadata()
    del metadata["content_sha256"]

    with pytest.raises(ValueError, match="content_sha256"):
        validate_chunk_metadata(metadata)


def test_build_qdrant_payload_contains_chunk_id_and_contract_metadata():
    metadata = _metadata()
    payload = build_qdrant_payload(
        chunk_id=UUID("00000000-0000-0000-0000-000000000004"),
        chunk_metadata=metadata,
    )

    assert payload["chunk_id"] == "00000000-0000-0000-0000-000000000004"
    assert payload["source_id"] == str(SOURCE_ID)
    assert payload["document_title"] == "Document fictif"
    assert payload["source_code"] == "source_fictive"
    assert payload["content_sha256"] == "abc123"


def test_normalize_document_metadata_accepts_valid_role_documentaire():
    metadata = normalize_document_metadata(_document_metadata())

    assert metadata["role_documentaire"] == "opposition"


def test_normalize_document_metadata_rejects_invalid_role_documentaire():
    with pytest.raises(ValueError, match="role_documentaire"):
        normalize_document_metadata(_document_metadata(role_documentaire="campagne"))


def test_normalize_document_metadata_accepts_valid_statut_metadonnees():
    metadata = normalize_document_metadata(
        _document_metadata(statut_metadonnees="BROUILLON")
    )

    assert metadata["statut_metadonnees"] == "brouillon"


def test_normalize_document_metadata_accepts_closed_document_values():
    metadata = normalize_document_metadata(
        _document_metadata(
            famille_politique="INSTITUTIONNEL",
            positionnement="CONTEXTUEL",
            niveau_confiance="MOYEN",
            type_document="rapport_institutionnel",
            usage_probatoire="contexte",
            mode_qualification="import_manifest",
        )
    )

    assert metadata["famille_politique"] == "institutionnel"
    assert metadata["positionnement"] == "contextuel"
    assert metadata["niveau_confiance"] == "moyen"
    assert metadata["type_document"] == "rapport_institutionnel"
    assert metadata["usage_probatoire"] == "contexte"
    assert metadata["mode_qualification"] == "import_manifest"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("famille_politique", "rn"),
        ("positionnement", "adversarial"),
        ("niveau_confiance", "primary"),
        ("type_document", "white_paper"),
        ("usage_probatoire", "official"),
        ("mode_qualification", "human"),
    ],
)
def test_normalize_document_metadata_rejects_invalid_closed_values(field, value):
    with pytest.raises(ValueError, match=field):
        normalize_document_metadata(_document_metadata(**{field: value}))


def test_normalize_document_metadata_normalizes_required_source_code():
    metadata = normalize_document_metadata(_document_metadata(source_code=" CNIL "))

    assert metadata["source_code"] == "cnil"


def test_normalize_document_metadata_rejects_missing_source_code():
    data = _document_metadata()
    del data["source_code"]

    with pytest.raises(ValueError, match="source_code"):
        normalize_document_metadata(data)


def test_normalize_document_metadata_normalizes_theme_tags():
    metadata = normalize_document_metadata(
        _document_metadata(theme_tags=[" ia ", "travail", ""])
    )

    assert metadata["theme_tags"] == ["ia", "travail"]


def test_normalize_document_metadata_rejects_missing_field():
    data = _document_metadata()
    del data["mode_qualification"]

    with pytest.raises(ValueError, match="mode_qualification"):
        normalize_document_metadata(data)


def test_normalize_document_metadata_serializes_confidence_to_float():
    metadata = normalize_document_metadata(
        _document_metadata(qualification_confidence=1, validated_at=None)
    )

    assert metadata["qualification_confidence"] == 1.0
    assert metadata["validated_at"] is None
