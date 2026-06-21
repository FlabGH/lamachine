from datetime import UTC, date, datetime
from uuid import UUID

import pytest

from app.services.documentary.metadata_contract import (
    build_canonical_chunk_metadata,
    build_chunk_metadata,
    build_qdrant_payload,
    missing_chunk_metadata_keys,
    normalize_document_metadata,
    normalize_ingestion_metadata,
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
        "extra": {
            "chunking_strategy": "word_window_v1",
            "chunking_version": "word_window_v1",
            "split_strategy": "word_window",
        },
    }
    data.update(overrides)
    return build_chunk_metadata(**data)


def test_build_chunk_metadata_serializes_ids_and_keeps_pages():
    metadata = _metadata()

    assert metadata["source_id"] == str(SOURCE_ID)
    assert metadata["document_id"] == str(DOCUMENT_ID)
    assert metadata["parent_document_id"] == str(DOCUMENT_ID)
    assert metadata["index_version_id"] == str(INDEX_VERSION_ID)
    assert metadata["document_title"] == "Document fictif"
    assert metadata["source_code"] == "source_fictive"
    assert metadata["content_hash"] == "abc123"
    assert metadata["page_start"] == 1
    assert metadata["page_end"] == 2
    assert metadata["chunking_strategy"] == "word_window_v1"
    assert metadata["chunking_version"] == "word_window_v1"
    assert metadata["split_strategy"] == "word_window"


def test_build_canonical_chunk_metadata_uses_registry_field_names():
    metadata = build_canonical_chunk_metadata(
        source_id=SOURCE_ID,
        document_id=DOCUMENT_ID,
        chunk_id=UUID("00000000-0000-0000-0000-000000000004"),
        title="Document fictif",
        source_code="source_fictive",
        content_hash="abc123",
        index_version=INDEX_VERSION_ID,
        vector_collection="test_collection",
        chunk_index=0,
        token_count=10,
        chunking_version="word_window_v1",
        chunking_strategy="word_window",
        chunk_size=450,
        chunk_overlap=80,
        page_start=1,
        page_end=2,
    )

    assert metadata["title"] == "Document fictif"
    assert metadata["content_hash"] == "abc123"
    assert metadata["index_version"] == str(INDEX_VERSION_ID)
    assert metadata["chunk_id"] == "00000000-0000-0000-0000-000000000004"
    assert "document_title" not in metadata
    assert "content_sha256" not in metadata
    assert "index_version_id" not in metadata


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
    assert payload["content_hash"] == "abc123"
    assert payload["chunking_version"] == "word_window_v1"


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


def test_normalize_document_metadata_normalizes_validated_at_iso_datetime():
    metadata = normalize_document_metadata(
        _document_metadata(validated_at="2026-05-30T00:00:00Z")
    )

    assert metadata["validated_at"] == "2026-05-30T00:00:00+00:00"


def test_normalize_document_metadata_rejects_invalid_validated_at():
    with pytest.raises(ValueError, match="validated_at"):
        normalize_document_metadata(_document_metadata(validated_at="30/05/2026"))


def test_normalize_ingestion_metadata_applies_defaults():
    metadata = normalize_ingestion_metadata({}, title="Document test", source_code=" SRC ")

    assert metadata["title"] == "Document test"
    assert metadata["source_code"] == "src"
    assert metadata["data_tags"] == ["corpus"]
    assert metadata["service_family"] == "transverse"
    assert metadata["service_ids"] == []
    assert metadata["visibility_scope"] == "public"
    assert metadata["access_level"] == "open"
    assert metadata["freshness_status"] == "unknown"
    assert metadata["language"] == "fr"
    assert metadata["is_primary_source"] is False
    assert metadata["citation_policy"] == "a_verifier"
    assert metadata["rights_status"] == "unknown"
    assert metadata["collected_at"]


def test_normalize_ingestion_metadata_accepts_enriched_values():
    metadata = normalize_ingestion_metadata(
        {
            "data_tags": [" WEB ", "juridique"],
            "service_family": "debat",
            "service_ids": ["I.1", "IV.1"],
            "visibility_scope": "organisation",
            "organization_id": " Parti-Test ",
            "access_level": "restricted",
            "source_url": "https://example.test/doc.pdf",
            "publication_date": "2026-06-01",
            "collected_at": "2026-06-02T10:00:00Z",
            "freshness_status": "current",
            "language": "fr",
            "geographic_scope": "France",
            "temporal_scope": "2025-2026",
            "is_primary_source": True,
            "citation_policy": "citable",
            "rights_status": "copyrighted",
        },
        title="Doc",
        source_code="PS",
    )

    assert metadata["data_tags"] == ["web", "juridique"]
    assert metadata["service_family"] == "debat"
    assert metadata["service_ids"] == ["I.1", "IV.1"]
    assert metadata["visibility_scope"] == "organisation"
    assert metadata["organization_id"] == "parti-test"
    assert metadata["access_level"] == "restricted"
    assert metadata["source_url"] == "https://example.test/doc.pdf"
    assert metadata["publication_date"] == "2026-06-01"
    assert metadata["collected_at"] == "2026-06-02T10:00:00+00:00"
    assert metadata["is_primary_source"] is True
    assert metadata["source_code"] == "ps"


def test_normalize_ingestion_metadata_rejects_invalid_data_tag():
    with pytest.raises(ValueError, match="data_tags"):
        normalize_ingestion_metadata({"data_tags": ["crawler"]})


def test_normalize_ingestion_metadata_requires_organization_id_for_org_scope():
    with pytest.raises(ValueError, match="organization_id"):
        normalize_ingestion_metadata({"visibility_scope": "organisation"})


def test_normalize_ingestion_metadata_accepts_python_date_values():
    metadata = normalize_ingestion_metadata(
        {
            "publication_date": date(2026, 6, 1),
            "collected_at": datetime(2026, 6, 2, 10, 30, tzinfo=UTC),
        }
    )

    assert metadata["publication_date"] == "2026-06-01"
    assert metadata["collected_at"] == "2026-06-02T10:30:00+00:00"


def test_normalize_ingestion_metadata_rejects_invalid_iso_date():
    with pytest.raises(ValueError, match="publication_date"):
        normalize_ingestion_metadata({"publication_date": "juin 2026"})


def test_normalize_document_metadata_keeps_enriched_metadata():
    metadata = normalize_document_metadata(
        _document_metadata(
            data_tags=["parlement"],
            service_family="rapport",
            service_ids=["XVI.1"],
            publication_date="2026-01-01",
            is_primary_source=True,
        )
    )

    assert metadata["data_tags"] == ["parlement"]
    assert metadata["service_family"] == "rapport"
    assert metadata["service_ids"] == ["XVI.1"]
    assert metadata["publication_date"] == "2026-01-01"
    assert metadata["is_primary_source"] is True


def test_build_qdrant_payload_inherits_ingestion_metadata():
    ingestion_metadata = normalize_ingestion_metadata(
        {
            "data_tags": ["interne"],
            "service_family": "crise",
            "service_ids": ["IV.1"],
            "visibility_scope": "restreint",
            "access_level": "admin",
        },
        title="Doc crise",
        source_code="interne",
    )
    ingestion_metadata.update(
        {
            "chunking_version": "word_window_v1",
            "split_strategy": "word_window",
        }
    )
    chunk_metadata = _metadata(extra=ingestion_metadata)
    payload = build_qdrant_payload(
        chunk_id=UUID("00000000-0000-0000-0000-000000000004"),
        chunk_metadata=chunk_metadata,
    )

    assert payload["data_tags"] == ["interne"]
    assert payload["service_family"] == "crise"
    assert payload["service_ids"] == ["IV.1"]
    assert payload["visibility_scope"] == "restreint"
    assert payload["access_level"] == "admin"
