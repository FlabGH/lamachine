from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass


PAGE_RE = re.compile(r"\[PAGE (?P<page>\d+)\]")
SECTION_RE = re.compile(r"\[SECTION (?P<section>[^\]]+)\]")
DEFAULT_CHUNKING_VERSION = "word_window_v1"
DEFAULT_SPLIT_STRATEGY = "word_window"
SUPPORTED_SPLIT_STRATEGIES = {DEFAULT_SPLIT_STRATEGY}


@dataclass(frozen=True)
class ChunkingConfig:
    chunk_size: int = 450
    chunk_overlap: int = 80
    split_strategy: str = DEFAULT_SPLIT_STRATEGY
    min_chunk_size: int = 80
    max_chunk_size: int = 650
    chunking_version: str = DEFAULT_CHUNKING_VERSION

    def __post_init__(self) -> None:
        if self.split_strategy not in SUPPORTED_SPLIT_STRATEGIES:
            raise ValueError(f"Unsupported split_strategy: {self.split_strategy}")
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if self.chunk_overlap < 0:
            raise ValueError("chunk_overlap must be greater than or equal to 0")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be lower than chunk_size")
        if self.min_chunk_size <= 0:
            raise ValueError("min_chunk_size must be greater than 0")
        if self.max_chunk_size < self.chunk_size:
            raise ValueError("max_chunk_size must be greater than or equal to chunk_size")
        if self.min_chunk_size > self.chunk_size:
            raise ValueError("min_chunk_size must be lower than or equal to chunk_size")
        if not self.chunking_version.strip():
            raise ValueError("chunking_version must not be empty")

    @classmethod
    def from_index_version(cls, index_version: dict) -> "ChunkingConfig":
        return cls(
            chunk_size=index_version["chunk_size"],
            chunk_overlap=index_version["chunk_overlap"],
            split_strategy=index_version.get("split_strategy")
            or index_version.get("chunking_strategy")
            or DEFAULT_SPLIT_STRATEGY,
            min_chunk_size=index_version.get("min_chunk_size") or 80,
            max_chunk_size=index_version.get("max_chunk_size")
            or max(index_version["chunk_size"], 650),
            chunking_version=index_version.get("chunking_version")
            or index_version.get("chunking_strategy")
            or DEFAULT_CHUNKING_VERSION,
        )

    def metadata(self) -> dict:
        return {
            "chunking_version": self.chunking_version,
            "split_strategy": self.split_strategy,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "min_chunk_size": self.min_chunk_size,
            "max_chunk_size": self.max_chunk_size,
        }


@dataclass(frozen=True)
class TextChunk:
    chunk_index: int
    content: str
    content_sha256: str
    page_start: int | None
    page_end: int | None
    token_count: int
    metadata: dict


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def estimate_tokens(text: str) -> int:
    return max(1, len(text.split()))


def detect_page_range(text: str) -> tuple[int | None, int | None]:
    pages = [int(m.group("page")) for m in PAGE_RE.finditer(text)]
    if not pages:
        return None, None
    return min(pages), max(pages)


def detect_section_title(text: str) -> str | None:
    matches = [m.group("section").strip() for m in SECTION_RE.finditer(text)]
    matches = [section for section in matches if section]
    if len(set(matches)) == 1:
        return matches[0]
    return None


def chunk_text(
    text: str,
    *,
    chunk_size_words: int = 450,
    chunk_overlap_words: int = 80,
    config: ChunkingConfig | None = None,
) -> list[TextChunk]:
    chunking_config = config or ChunkingConfig(
        chunk_size=chunk_size_words,
        chunk_overlap=chunk_overlap_words,
        min_chunk_size=min(80, chunk_size_words),
        max_chunk_size=max(650, chunk_size_words),
    )
    words = text.split()
    if not words:
        return []

    chunks: list[TextChunk] = []
    start = 0
    chunk_index = 0

    while start < len(words):
        end = min(start + chunking_config.chunk_size, len(words))
        remaining_words = len(words) - end
        if (
            0 < remaining_words < chunking_config.min_chunk_size
            and len(words) - start <= chunking_config.max_chunk_size
        ):
            end = len(words)
        content = " ".join(words[start:end]).strip()
        page_start, page_end = detect_page_range(content)
        section_title = detect_section_title(content)
        metadata = {
            **chunking_config.metadata(),
            "chunking_strategy": chunking_config.chunking_version,
            "chunk_size_words": chunking_config.chunk_size,
            "chunk_overlap_words": chunking_config.chunk_overlap,
        }
        if section_title:
            metadata["section_title"] = section_title

        chunks.append(
            TextChunk(
                chunk_index=chunk_index,
                content=content,
                content_sha256=sha256_text(content),
                page_start=page_start,
                page_end=page_end,
                token_count=estimate_tokens(content),
                metadata=metadata,
            )
        )

        chunk_index += 1
        if end >= len(words):
            break
        start = end - chunking_config.chunk_overlap

    return chunks
