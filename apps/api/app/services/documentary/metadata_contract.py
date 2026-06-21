from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any


ROLE_DOCUMENTAIRE_VALUES = {
    "cadrage_institutionnel",
    "doctrine_centrale",
    "doctrine_alliee",
    "doctrine_ethique",
    "doctrine_sectorielle",
    "source_factuelle",
    "opposition",
    "contexte_mediatique",
    "cadre_juridique",
    "arbitrage_interne",
    "presse_analyse",
}

FAMILLE_POLITIQUE_VALUES = {
    "doctrine_sociale_chretienne",
    "gauche_progressiste",
    "gauche_radicale",
    "gauche_social_democrate",
    "extreme_droite",
    "droite",
    "centre",
    "institutionnel",
    "institution_republicaine",
    "academique",
    "media_reference",
    "presse",
    "autre",
    "reformisme_public",
}

POSITION_PROJET_VALUES = {
    "allie",
    "reference",
    "aligne",
    "allie_critique",
    "appui",
    "adversaire",
    "inspiration",
    "neutre",
    "observation",
    "contextuel",
}

NIVEAU_CONFIANCE_VALUES = {
    "eleve",
    "moyen",
    "faible",
    "inconnu",
}

TYPE_DOCUMENT_VALUES = {
    "essai_doctrinal",
    "programme_politique",
    "note_programmatique",
    "rapport_expertise",
    "rapport_public",
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
    "audit",
    "preuve_directe",
    "position_officielle",
    "analyse",
    "contexte",
    "recommandations",
    "a_verifier",
}

DATA_TAG_VALUES = {
    "web",
    "presse",
    "sondages",
    "electoral",
    "insee",
    "juridique",
    "parlement",
    "social",
    "corpus",
    "interne",
    "aucune",
}

SERVICE_FAMILY_VALUES = {
    "bibliotheque",
    "programme",
    "discours",
    "debat",
    "crise",
    "territoire",
    "interview",
    "presse",
    "rapport",
    "transverse",
    "autre",
}

VISIBILITY_SCOPE_VALUES = {
    "public",
    "interne",
    "restreint",
    "organisation",
}

ACCESS_LEVEL_VALUES = {
    "open",
    "authenticated",
    "restricted",
    "admin",
}

FRESHNESS_STATUS_VALUES = {
    "current",
    "stale",
    "archived",
    "unknown",
}

LANGUAGE_VALUES = {
    "fr",
    "en",
    "multi",
    "unknown",
}

CITATION_POLICY_VALUES = {
    "citable",
    "non_citable",
    "interne_only",
    "a_verifier",
}

RIGHTS_STATUS_VALUES = {
    "open",
    "copyrighted",
    "internal",
    "unknown",
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
    "data_tags",
    "service_family",
    "service_ids",
    "visibility_scope",
    "organization_id",
    "access_level",
    "source_url",
    "publication_date",
    "collected_at",
    "freshness_status",
    "language",
    "geographic_scope",
    "temporal_scope",
    "is_primary_source",
    "citation_policy",
    "rights_status",
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


def _normalize_optional_free_text(metadata: dict[str, Any], key: str) -> str | None:
    value = metadata.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"Invalid document metadata key: {key}")
    normalized = value.strip()
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


def _normalize_optional_enum(
    metadata: dict[str, Any],
    key: str,
    allowed_values: set[str],
    default: str,
) -> str:
    value = metadata.get(key)
    if value is None:
        return default
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Invalid document metadata key: {key}")
    normalized = value.strip().lower()
    if normalized not in allowed_values:
        raise ValueError(
            f"Invalid document metadata value for {key}: {normalized}. "
            f"Allowed values: {', '.join(sorted(allowed_values))}"
        )
    return normalized


def _normalize_optional_string_list(
    metadata: dict[str, Any],
    key: str,
    *,
    default: list[str],
    allowed_values: set[str] | None = None,
    lowercase: bool = True,
) -> list[str]:
    value = metadata.get(key)
    if value is None:
        return list(default)
    if not isinstance(value, list):
        raise ValueError(f"Invalid document metadata key: {key}")

    normalized_items = []
    for item in value:
        if not isinstance(item, str):
            raise ValueError(f"{key} must contain only strings")
        normalized = item.strip()
        if lowercase:
            normalized = normalized.lower()
        if not normalized:
            continue
        if allowed_values is not None and normalized not in allowed_values:
            raise ValueError(
                f"Invalid document metadata value for {key}: {normalized}. "
                f"Allowed values: {', '.join(sorted(allowed_values))}"
            )
        normalized_items.append(normalized)

    return normalized_items


def _normalize_optional_bool(
    metadata: dict[str, Any],
    key: str,
    default: bool,
) -> bool:
    value = metadata.get(key)
    if value is None:
        return default
    if not isinstance(value, bool):
        raise ValueError(f"Invalid document metadata key: {key}")
    return value


def _normalize_optional_iso_date_text(metadata: dict[str, Any], key: str) -> str | None:
    value = metadata.get(key)
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Invalid document metadata key: {key}")

    raw_value = value.strip()
    try:
        if "T" in raw_value:
            return datetime.fromisoformat(raw_value.replace("Z", "+00:00")).isoformat()
        return date.fromisoformat(raw_value).isoformat()
    except ValueError as exc:
        raise ValueError(f"Invalid ISO date metadata key: {key}") from exc


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
        "validated_at": _normalize_optional_iso_date_text(metadata, "validated_at"),
        "theme_tags": _normalize_theme_tags(metadata),
    }

    ingestion_metadata = normalize_ingestion_metadata(
        metadata,
        title=normalized["title"],
        source_code=normalized["source_code"],
    )

    return {
        **ingestion_metadata,
        **normalized,
    }


def normalize_ingestion_metadata(
    metadata: dict[str, Any] | None,
    *,
    title: str | None = None,
    source_code: str | None = None,
) -> dict[str, Any]:
    source = metadata or {}
    normalized: dict[str, Any] = {
        "data_tags": _normalize_optional_string_list(
            source,
            "data_tags",
            default=["corpus"],
            allowed_values=DATA_TAG_VALUES,
        ),
        "service_family": _normalize_optional_enum(
            source,
            "service_family",
            SERVICE_FAMILY_VALUES,
            "transverse",
        ),
        "service_ids": _normalize_optional_string_list(
            source,
            "service_ids",
            default=[],
            lowercase=False,
        ),
        "visibility_scope": _normalize_optional_enum(
            source,
            "visibility_scope",
            VISIBILITY_SCOPE_VALUES,
            "public",
        ),
        "organization_id": _normalize_optional_text(source, "organization_id"),
        "access_level": _normalize_optional_enum(
            source,
            "access_level",
            ACCESS_LEVEL_VALUES,
            "open",
        ),
        "source_url": _normalize_optional_free_text(source, "source_url"),
        "publication_date": _normalize_optional_iso_date_text(source, "publication_date"),
        "collected_at": _normalize_optional_iso_date_text(source, "collected_at")
        or datetime.now(UTC).isoformat(),
        "freshness_status": _normalize_optional_enum(
            source,
            "freshness_status",
            FRESHNESS_STATUS_VALUES,
            "unknown",
        ),
        "language": _normalize_optional_enum(
            source,
            "language",
            LANGUAGE_VALUES,
            "fr",
        ),
        "geographic_scope": _normalize_optional_free_text(
            source,
            "geographic_scope",
        ),
        "temporal_scope": _normalize_optional_free_text(source, "temporal_scope"),
        "is_primary_source": _normalize_optional_bool(
            source,
            "is_primary_source",
            False,
        ),
        "citation_policy": _normalize_optional_enum(
            source,
            "citation_policy",
            CITATION_POLICY_VALUES,
            "a_verifier",
        ),
        "rights_status": _normalize_optional_enum(
            source,
            "rights_status",
            RIGHTS_STATUS_VALUES,
            "unknown",
        ),
    }

    if title is not None:
        normalized["title"] = title.strip() if title.strip() else title
    if source_code is not None:
        normalized["source_code"] = source_code.strip().lower()

    if normalized["visibility_scope"] == "organisation" and not normalized["organization_id"]:
        raise ValueError(
            "organization_id is required when visibility_scope is organisation"
        )

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


def build_canonical_chunk_metadata(
    *,
    source_id: Any,
    document_id: Any,
    chunk_id: Any,
    title: str,
    source_code: str,
    content_hash: str,
    index_version: Any,
    vector_collection: str,
    chunk_index: int,
    token_count: int,
    chunking_version: str,
    chunking_strategy: str,
    chunk_size: int,
    chunk_overlap: int,
    parent_document_id: Any | None = None,
    page_start: int | None = None,
    page_end: int | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metadata = {
        **(extra or {}),
        "source_id": str(source_id),
        "document_id": str(document_id),
        "parent_document_id": str(parent_document_id or document_id),
        "chunk_id": str(chunk_id),
        "title": title,
        "source_code": source_code,
        "content_hash": content_hash,
        "index_version": str(index_version),
        "vector_collection": vector_collection,
        "chunk_index": chunk_index,
        "token_count": token_count,
        "chunking_version": chunking_version,
        "chunking_strategy": chunking_strategy,
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
    }
    if page_start is not None:
        metadata["page_start"] = page_start
    if page_end is not None:
        metadata["page_end"] = page_end
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
