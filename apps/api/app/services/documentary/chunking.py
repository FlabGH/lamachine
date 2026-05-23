from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass


PAGE_RE = re.compile(r"\[PAGE (?P<page>\d+)\]")


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


def chunk_text(
    text: str,
    *,
    chunk_size_words: int = 450,
    chunk_overlap_words: int = 80,
) -> list[TextChunk]:
    words = text.split()
    if not words:
        return []

    chunks: list[TextChunk] = []
    start = 0
    chunk_index = 0

    while start < len(words):
        end = min(start + chunk_size_words, len(words))
        content = " ".join(words[start:end]).strip()
        page_start, page_end = detect_page_range(content)

        chunks.append(
            TextChunk(
                chunk_index=chunk_index,
                content=content,
                content_sha256=sha256_text(content),
                page_start=page_start,
                page_end=page_end,
                token_count=estimate_tokens(content),
                metadata={
                    "chunking_strategy": "word_window_v1",
                    "chunk_size_words": chunk_size_words,
                    "chunk_overlap_words": chunk_overlap_words,
                },
            )
        )

        chunk_index += 1
        if end >= len(words):
            break
        start = end - chunk_overlap_words

    return chunks
