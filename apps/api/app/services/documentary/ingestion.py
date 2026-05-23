from __future__ import annotations

import hashlib
from pathlib import Path

from pypdf import PdfReader


STORAGE_DIR = Path("/tmp/lamachine_uploads")
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def save_uploaded_file(filename: str, content: bytes) -> tuple[str, str]:
    digest = sha256_bytes(content)
    safe_name = filename.replace("/", "_").replace("\\", "_")
    path = STORAGE_DIR / f"{digest}_{safe_name}"
    path.write_bytes(content)
    return str(path), digest


def extract_pdf_text(path: str) -> str:
    reader = PdfReader(path)
    pages: list[str] = []

    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            pages.append(f"\n\n[PAGE {i}]\n{text}")

    return "\n".join(pages).strip()


def normalize_text(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.splitlines()).strip()
