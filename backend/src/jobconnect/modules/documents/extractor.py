"""Text extraction from uploaded document files.

Slice 5 supports PDF via pypdf. DOCX returns empty string (Slice 6 scope).
Any extraction failure returns empty string so the worker can mark the job failed.
"""
from __future__ import annotations

import io
from typing import BinaryIO


def extract_text(stream: BinaryIO, mime_type: str) -> str:
    """Extract plain text from a file stream. Returns empty string on failure."""
    data = stream.read()
    if mime_type == "application/pdf":
        return _extract_pdf(data)
    # DOCX and other types: no extractor in Slice 5.
    return ""


def _extract_pdf(data: bytes) -> str:
    try:
        import pypdf  # type: ignore[import]

        reader = pypdf.PdfReader(io.BytesIO(data))
        parts: list[str] = []
        for page in reader.pages:
            text = page.extract_text() or ""
            parts.append(text)
        return "\n".join(parts)
    except Exception:
        return ""
