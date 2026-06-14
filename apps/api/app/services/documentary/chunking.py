from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass


PAGE_RE = re.compile(r"\[PAGE (?P<page>\d+)\]")
SECTION_RE = re.compile(r"\[SECTION (?P<section>[^\]]+)\]")
DEFAULT_CHUNKING_VERSION = "word_window_v1"
DEFAULT_SPLIT_STRATEGY = "word_window"
STRUCTURAL_SPLIT_STRATEGY = "section_aware_window"
STRUCTURAL_CHUNKING_VERSION = "section_aware_window_v1"
SUPPORTED_SPLIT_STRATEGIES = {DEFAULT_SPLIT_STRATEGY, STRUCTURAL_SPLIT_STRATEGY}
MARKDOWN_HEADING_RE = re.compile(r"^(?P<marks>#{1,4})\s+(?P<title>.+)$")
NUMBERED_HEADING_RE = re.compile(r"^(?P<number>\d+(?:\.\d+){0,3})[.)]?\s+(?P<title>.+)$")
NAMED_HEADING_RE = re.compile(
    r"^(?P<prefix>chapitre|partie|section|titre)\s+"
    r"(?P<label>[ivxlcdm\d]+(?:\s*[-:]\s*.+)?)$",
    re.IGNORECASE,
)
MAX_HEADING_CHARS = 120
MAX_HEADING_WORDS = 16


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


@dataclass
class _StructuralSection:
    title: str | None
    heading_path: list[str]
    section_level: int | None
    lines: list[str]
    pages: list[int]


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


def _base_chunk_metadata(chunking_config: ChunkingConfig) -> dict:
    return {
        **chunking_config.metadata(),
        "chunking_strategy": chunking_config.chunking_version,
        "chunk_size_words": chunking_config.chunk_size,
        "chunk_overlap_words": chunking_config.chunk_overlap,
    }


def _chunk_words(
    text: str,
    *,
    chunking_config: ChunkingConfig,
    start_index: int = 0,
    extra_metadata: dict | None = None,
) -> list[TextChunk]:
    words = text.split()
    if not words:
        return []

    chunks: list[TextChunk] = []
    start = 0
    chunk_index = start_index

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
        metadata = _base_chunk_metadata(chunking_config)
        if extra_metadata:
            metadata.update(extra_metadata)
        if section_title and "section_title" not in metadata:
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


def _clean_heading_title(raw_title: str) -> str:
    return " ".join(raw_title.strip().strip("#").split())


def _is_probable_heading(title: str) -> bool:
    title = _clean_heading_title(title)
    if not title:
        return False
    if len(title) > MAX_HEADING_CHARS:
        return False
    words = title.split()
    if len(words) > MAX_HEADING_WORDS:
        return False
    if title.endswith((".", ",", ";")):
        return False
    alnum_count = sum(1 for char in title if char.isalnum())
    if alnum_count < max(3, len(title) * 0.45):
        return False
    if title.isdigit():
        return False
    return True


def _detect_heading(line: str) -> tuple[int, str] | None:
    stripped = line.strip()
    if not stripped:
        return None

    section_match = SECTION_RE.fullmatch(stripped)
    if section_match:
        title = _clean_heading_title(section_match.group("section"))
        return (1, title) if _is_probable_heading(title) else None

    markdown_match = MARKDOWN_HEADING_RE.fullmatch(stripped)
    if markdown_match:
        title = _clean_heading_title(markdown_match.group("title"))
        return (len(markdown_match.group("marks")), title) if _is_probable_heading(title) else None

    numbered_match = NUMBERED_HEADING_RE.fullmatch(stripped)
    if numbered_match:
        title = _clean_heading_title(stripped)
        level = min(4, numbered_match.group("number").count(".") + 1)
        return (level, title) if _is_probable_heading(title) else None

    named_match = NAMED_HEADING_RE.fullmatch(stripped)
    if named_match:
        title = _clean_heading_title(stripped)
        return (1, title) if _is_probable_heading(title) else None

    if _is_probable_heading(stripped):
        has_title_case = sum(1 for word in stripped.split() if word[:1].isupper()) >= 2
        has_upper_signal = stripped.isupper()
        if has_title_case or has_upper_signal:
            return 2, stripped

    return None


def _extract_pages_from_line(line: str) -> tuple[list[int], str]:
    pages = [int(match.group("page")) for match in PAGE_RE.finditer(line)]
    line_without_pages = PAGE_RE.sub("", line).strip()
    return pages, line_without_pages


def _parse_structural_sections(text: str) -> tuple[list[_StructuralSection], list[str]]:
    sections: list[_StructuralSection] = []
    warnings: list[str] = []
    heading_stack: list[tuple[int, str]] = []
    current = _StructuralSection(
        title=None,
        heading_path=[],
        section_level=None,
        lines=[],
        pages=[],
    )
    current_pages: list[int] = []

    def finish_current() -> None:
        if current.lines:
            sections.append(
                _StructuralSection(
                    title=current.title,
                    heading_path=list(current.heading_path),
                    section_level=current.section_level,
                    lines=list(current.lines),
                    pages=list(current.pages),
                )
            )

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        pages, line_without_pages = _extract_pages_from_line(line)
        if pages:
            current_pages = pages
        line = line_without_pages
        if not line:
            continue

        heading = _detect_heading(line)
        if heading:
            finish_current()
            level, title = heading
            heading_stack = [
                (existing_level, existing_title)
                for existing_level, existing_title in heading_stack
                if existing_level < level
            ]
            heading_stack.append((level, title))
            current = _StructuralSection(
                title=title,
                heading_path=[item_title for _, item_title in heading_stack],
                section_level=level,
                lines=[],
                pages=list(current_pages),
            )
            continue

        current.lines.append(line)
        current.pages.extend(current_pages)

    finish_current()

    usable_sections = [section for section in sections if section.lines]
    if len(usable_sections) < 2:
        warnings.append("insufficient_structure")
    return usable_sections, warnings


def _format_structural_section_text(section: _StructuralSection) -> str:
    body = " ".join(" ".join(section.lines).split()).strip()
    if not section.heading_path:
        return body
    heading = " > ".join(section.heading_path)
    return f"[SECTION {heading}] {body}".strip()


def _chunk_section_aware(text: str, *, chunking_config: ChunkingConfig) -> list[TextChunk]:
    sections, warnings = _parse_structural_sections(text)
    if warnings:
        fallback_metadata = {
            "structural_chunking_status": "fallback_word_window",
            "structural_chunking_warnings": warnings,
        }
        return _chunk_words(
            text,
            chunking_config=ChunkingConfig(
                chunk_size=chunking_config.chunk_size,
                chunk_overlap=chunking_config.chunk_overlap,
                split_strategy=DEFAULT_SPLIT_STRATEGY,
                min_chunk_size=chunking_config.min_chunk_size,
                max_chunk_size=chunking_config.max_chunk_size,
                chunking_version=chunking_config.chunking_version,
            ),
            extra_metadata=fallback_metadata,
        )

    chunks: list[TextChunk] = []
    next_index = 0
    for section in sections:
        content = _format_structural_section_text(section)
        page_start = min(section.pages) if section.pages else detect_page_range(content)[0]
        page_end = max(section.pages) if section.pages else detect_page_range(content)[1]
        section_metadata = {
            "structural_chunking_status": "section_aware",
            "section_title": section.title,
            "heading_path": section.heading_path,
            "section_level": section.section_level,
        }
        section_chunks = _chunk_words(
            content,
            chunking_config=chunking_config,
            start_index=next_index,
            extra_metadata=section_metadata,
        )
        for chunk in section_chunks:
            chunk_page_start = chunk.page_start or page_start
            chunk_page_end = chunk.page_end or page_end
            chunks.append(
                TextChunk(
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    content_sha256=chunk.content_sha256,
                    page_start=chunk_page_start,
                    page_end=chunk_page_end,
                    token_count=chunk.token_count,
                    metadata=chunk.metadata,
                )
            )
        next_index += len(section_chunks)

    return chunks


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
    if chunking_config.split_strategy == STRUCTURAL_SPLIT_STRATEGY:
        return _chunk_section_aware(text, chunking_config=chunking_config)
    return _chunk_words(text, chunking_config=chunking_config)


def deduplicate_chunks(chunks: list[TextChunk]) -> list[TextChunk]:
    seen_hashes: set[str] = set()
    unique_chunks: list[TextChunk] = []

    for chunk in chunks:
        if chunk.content_sha256 in seen_hashes:
            continue
        seen_hashes.add(chunk.content_sha256)
        unique_chunks.append(chunk)

    return unique_chunks
