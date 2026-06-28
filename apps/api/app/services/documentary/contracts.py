from __future__ import annotations

from typing import TypeAlias
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, JsonValue, field_validator, model_validator


Metadata: TypeAlias = dict[str, JsonValue]


def _normalized_text(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


class DocumentaryContract(BaseModel):
    """Strict base class for documentary internal contracts."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class SourceReference(DocumentaryContract):
    source_id: UUID | None = None
    source_code: str

    @field_validator("source_code")
    @classmethod
    def normalize_source_code(cls, value: str) -> str:
        return _normalized_text(value, "source_code").lower()


class SourceSpan(DocumentaryContract):
    page_start: int | None = Field(default=None, ge=1)
    page_end: int | None = Field(default=None, ge=1)
    section_title: str | None = None

    @field_validator("section_title")
    @classmethod
    def normalize_section_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _normalized_text(value, "section_title")

    @model_validator(mode="after")
    def validate_page_range(self) -> "SourceSpan":
        if (self.page_start is None) != (self.page_end is None):
            raise ValueError("page_start and page_end must be provided together")
        if (
            self.page_start is not None
            and self.page_end is not None
            and self.page_end < self.page_start
        ):
            raise ValueError("page_end must be greater than or equal to page_start")
        return self


class DocumentInput(DocumentaryContract):
    source: SourceReference
    title: str
    mime_type: str
    filename: str | None = None
    raw_text: str
    metadata: Metadata = Field(default_factory=dict)

    @field_validator("title", "mime_type")
    @classmethod
    def normalize_required_fields(cls, value: str, info) -> str:
        return _normalized_text(value, info.field_name)

    @field_validator("filename")
    @classmethod
    def normalize_filename(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _normalized_text(value, "filename")


class DocumentRecord(DocumentaryContract):
    document_id: UUID
    source: SourceReference
    title: str
    mime_type: str
    filename: str | None = None
    status: str
    content_sha256: str
    raw_text: str | None = None
    metadata: Metadata = Field(default_factory=dict)

    @field_validator("title", "mime_type", "status", "content_sha256")
    @classmethod
    def normalize_required_fields(cls, value: str, info) -> str:
        return _normalized_text(value, info.field_name)


class ChunkPayload(DocumentaryContract):
    content: str
    content_sha256: str
    token_count: int = Field(ge=1)
    source_span: SourceSpan = Field(default_factory=SourceSpan)
    metadata: Metadata = Field(default_factory=dict)

    @field_validator("content", "content_sha256")
    @classmethod
    def normalize_required_fields(cls, value: str, info) -> str:
        return _normalized_text(value, info.field_name)


class ChunkRecord(DocumentaryContract):
    chunk_id: UUID
    document_id: UUID
    index_version_id: UUID
    chunk_index: int = Field(ge=0)
    payload: ChunkPayload
    qdrant_point_id: UUID | None = None


class StructuredObjectProducer(DocumentaryContract):
    name: str
    version: str | None = None
    parameters: Metadata = Field(default_factory=dict)

    @field_validator("name", "version")
    @classmethod
    def normalize_text_fields(cls, value: str | None, info) -> str | None:
        if value is None:
            return None
        return _normalized_text(value, info.field_name)


class StructuredObjectPayload(DocumentaryContract):
    object_type: str
    title: str | None = None
    content: str
    source_span: SourceSpan = Field(default_factory=SourceSpan)
    metadata: Metadata = Field(default_factory=dict)
    confidence: float | None = Field(default=None, ge=0, le=1)

    @field_validator("object_type")
    @classmethod
    def normalize_object_type(cls, value: str) -> str:
        return _normalized_text(value, "object_type").lower()

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _normalized_text(value, "title")

    @field_validator("content")
    @classmethod
    def normalize_content(cls, value: str) -> str:
        return _normalized_text(value, "content")


class StructuredObjectInput(DocumentaryContract):
    document_id: UUID
    payload: StructuredObjectPayload
    producer: StructuredObjectProducer
    source_chunk_ids: list[UUID] = Field(default_factory=list)

    @field_validator("source_chunk_ids")
    @classmethod
    def reject_duplicate_source_chunks(cls, value: list[UUID]) -> list[UUID]:
        if len(value) != len(set(value)):
            raise ValueError("source_chunk_ids must not contain duplicates")
        return value


class StructuredObjectRecord(StructuredObjectInput):
    object_id: UUID
    qdrant_point_id: UUID | None = None


class MetadataFilters(DocumentaryContract):
    values: dict[str, list[str]] = Field(default_factory=dict)

    @field_validator("values")
    @classmethod
    def normalize_values(cls, value: dict[str, list[str]]) -> dict[str, list[str]]:
        normalized_filters: dict[str, list[str]] = {}
        for field_name, raw_values in value.items():
            normalized_field_name = _normalized_text(field_name, "filter field")
            if not isinstance(raw_values, list):
                raise ValueError(f"{normalized_field_name} filter values must be a list")

            normalized_values: list[str] = []
            for raw_value in raw_values:
                if not isinstance(raw_value, str):
                    raise ValueError(
                        f"{normalized_field_name} filter values must be strings"
                    )
                normalized_value = _normalized_text(
                    raw_value,
                    f"{normalized_field_name} filter value",
                )
                if normalized_value not in normalized_values:
                    normalized_values.append(normalized_value)

            if not normalized_values:
                raise ValueError(
                    f"{normalized_field_name} filter must contain at least one value"
                )
            normalized_filters[normalized_field_name] = normalized_values

        return normalized_filters


class RetrievalQuery(DocumentaryContract):
    query: str
    index_version_id: UUID
    top_k: int = Field(ge=1)
    rerank_top_k: int = Field(ge=1)
    filters: MetadataFilters = Field(default_factory=MetadataFilters)

    @field_validator("query")
    @classmethod
    def normalize_query(cls, value: str) -> str:
        return _normalized_text(value, "query")


class RetrievalScores(DocumentaryContract):
    dense_score: float | None = None
    lexical_score: float | None = None
    rerank_score: float | None = None


class RetrievalHit(DocumentaryContract):
    chunk_id: UUID
    document_id: UUID
    source: SourceReference
    source_span: SourceSpan = Field(default_factory=SourceSpan)
    rank_initial: int | None = Field(default=None, ge=1)
    rank_final: int = Field(ge=1)
    content: str
    metadata: Metadata = Field(default_factory=dict)
    scores: RetrievalScores = Field(default_factory=RetrievalScores)

    @field_validator("content")
    @classmethod
    def normalize_content(cls, value: str) -> str:
        return _normalized_text(value, "content")
