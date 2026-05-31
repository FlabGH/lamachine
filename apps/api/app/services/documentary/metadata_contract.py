from __future__ import annotations

from typing import Any


ROLE_DOCUMENTAIRE_VALUES = {
    "doctrine_centrale",
    "doctrine_alliee",
    "source_factuelle",
    "opposition",
    "contexte_mediatique",
    "cadre_juridique",
    "arbitrage_interne",
}

FAMILLE_POLITIQUE_VALUES = {
    "gauche_progressiste",
    "gauche_radicale",
    "extreme_droite",
    "droite",
    "centre",
    "institutionnel",
    "academique",
    "presse",
    "autre",
}

POSITION_PROJET_VALUES = {
    "reference",
    "aligne",
    "allie_critique",
    "adversaire",
    "neutre",
    "contextuel",
}

NIVEAU_CONFIANCE_VALUES = {
    "eleve",
    "moyen",
    "faible",
    "inconnu",
}

TYPE_DOCUMENT_VALUES = {
    "programme_politique",
    "note_programmatique",
    "rapport_think_tank",
    "rapport_institutionnel",
    "texte_juridique",
    "article_presse",
    "entretien",
    "discours",
    "tribune",
    "article_academique",
    "note_interne",
    "jeu_de_donnees",
    "autre",
}

STATUT_METADONNEES_VALUES = {
    "brouillon",
    "propose_ia",
    "valide_humain",
    "rejete",
}

MODE_QUALIFICATION_VALUES = {
    "manuel",
    "ia",
    "import_manifest",
}

USAGE_PROBATOIRE_VALUES = {
    "preuve_directe",
    "position_officielle",
    "analyse",
    "contexte",
    "a_verifier",
}

DOCUMENT_METADATA_KEYS = {
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
    "qualification_confidence",
    "qualification_rationale",
    "validated_by",
    "validated_at",
    "theme_tags",
}

CRITICAL_CHUNK_METADATA_KEYS = {
    "source_id",
    "document_id",
    "document_title",
    "source_code",
    "content_sha256",
    "content_hash",
    "index_version_id",
    "vector_collection",
    "chunking_version",
    "split_strategy",
    "parent_document_id",
}


def _normalize_required_text(metadata: dict[str, Any], key: str) -> str:
    value = metadata.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Missing or invalid document metadata key: {key}")
    return value.strip()


def _normalize_optional_text(metadata: dict[str, Any], key: str) -> str | None:
    value = metadata.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"Invalid document metadata key: {key}")
    normalized = value.strip().lower()
    return normalized or None


def _normalize_enum(
    metadata: dict[str, Any],
    key: str,
    allowed_values: set[str],
) -> str:
    value = _normalize_required_text(metadata, key).lower()
    if value not in allowed_values:
        raise ValueError(
            f"Invalid document metadata value for {key}: {value}. "
            f"Allowed values: {', '.join(sorted(allowed_values))}"
        )
    return value


def _normalize_theme_tags(metadata: dict[str, Any]) -> list[str]:
    value = metadata.get("theme_tags")
    if not isinstance(value, list):
        raise ValueError("Missing or invalid document metadata key: theme_tags")

    tags = []
    for item in value:
        if not isinstance(item, str):
            raise ValueError("theme_tags must contain only strings")
        tag = item.strip()
        if tag:
            tags.append(tag)

    return tags


def _normalize_qualification_confidence(metadata: dict[str, Any]) -> float:
    value = metadata.get("qualification_confidence")
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(
            "Missing or invalid document metadata key: qualification_confidence"
        )
    return float(value)


def normalize_document_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    normalized = {
        "title": _normalize_required_text(metadata, "title"),
        "source_code": _normalize_required_text(metadata, "source_code").lower(),
        "role_documentaire": _normalize_enum(
            metadata,
            "role_documentaire",
            ROLE_DOCUMENTAIRE_VALUES,
        ),
        "famille_politique": _normalize_enum(
            metadata,
            "famille_politique",
            FAMILLE_POLITIQUE_VALUES,
        ),
        "positionnement": _normalize_enum(
            metadata,
            "positionnement",
            POSITION_PROJET_VALUES,
        ),
        "niveau_confiance": _normalize_enum(
            metadata,
            "niveau_confiance",
            NIVEAU_CONFIANCE_VALUES,
        ),
        "type_document": _normalize_enum(
            metadata,
            "type_document",
            TYPE_DOCUMENT_VALUES,
        ),
        "usage_probatoire": _normalize_enum(
            metadata,
            "usage_probatoire",
            USAGE_PROBATOIRE_VALUES,
        ),
        "statut_metadonnees": _normalize_enum(
            metadata,
            "statut_metadonnees",
            STATUT_METADONNEES_VALUES,
        ),
        "mode_qualification": _normalize_enum(
            metadata,
            "mode_qualification",
            MODE_QUALIFICATION_VALUES,
        ),
        "qualification_confidence": _normalize_qualification_confidence(metadata),
        "qualification_rationale": _normalize_required_text(
            metadata,
            "qualification_rationale",
        ),
        "validated_by": _normalize_required_text(metadata, "validated_by"),
        "validated_at": metadata.get("validated_at"),
        "theme_tags": _normalize_theme_tags(metadata),
    }

    if normalized["validated_at"] is not None and not isinstance(
        normalized["validated_at"], str
    ):
        raise ValueError("validated_at must be null or a string")

    return normalized


def build_chunk_metadata(
    *,
    source_id: Any,
    document_id: Any,
    document_title: str,
    source_code: str,
    content_sha256: str,
    index_version_id: Any,
    vector_collection: str,
    parent_document_id: Any | None = None,
    page_start: int | None = None,
    page_end: int | None = None,
    section: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metadata = {
        **(extra or {}),
        "source_id": str(source_id),
        "document_id": str(document_id),
        "parent_document_id": str(parent_document_id or document_id),
        "document_title": document_title,
        "source_code": source_code,
        "content_sha256": content_sha256,
        "content_hash": content_sha256,
        "index_version_id": str(index_version_id),
        "vector_collection": vector_collection,
    }

    if page_start is not None:
        metadata["page_start"] = page_start
    if page_end is not None:
        metadata["page_end"] = page_end

    if page_start is None and page_end is None:
        metadata["section"] = section or "body"
    elif section:
        metadata["section"] = section

    return metadata


def missing_chunk_metadata_keys(metadata: dict[str, Any]) -> list[str]:
    missing = [
        key
        for key in sorted(CRITICAL_CHUNK_METADATA_KEYS)
        if metadata.get(key) in (None, "")
    ]

    has_page = metadata.get("page_start") is not None or metadata.get("page_end") is not None
    has_section = bool(metadata.get("section"))
    if not has_page and not has_section:
        missing.append("page_or_section")

    return missing


def validate_chunk_metadata(metadata: dict[str, Any]) -> None:
    missing = missing_chunk_metadata_keys(metadata)
    if missing:
        raise ValueError(f"Missing chunk metadata keys: {', '.join(missing)}")


def build_qdrant_payload(
    *,
    chunk_id: Any,
    chunk_metadata: dict[str, Any],
) -> dict[str, Any]:
    validate_chunk_metadata(chunk_metadata)
    return {
        "chunk_id": str(chunk_id),
        **chunk_metadata,
    }
