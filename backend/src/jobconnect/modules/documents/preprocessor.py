"""Text preprocessing: NFC normalization, control-char removal, whitespace cleanup.

Required per REQUIREMENTS.md §5.2 before any structured parsing or embedding.
"""
from __future__ import annotations

import re
import unicodedata


def preprocess_text(text: str) -> str:
    """Normalize text for downstream parsing and embedding.

    Steps:
    - NFC Unicode normalization (critical for Vietnamese diacritics).
    - Remove null bytes and non-printable control chars (keep \\n, \\t).
    - Collapse 3+ consecutive blank lines to 2.
    - Collapse runs of spaces/tabs within a line to a single space.
    """
    text = unicodedata.normalize("NFC", text)
    # Remove null bytes and control chars except LF (0x0a) and TAB (0x09)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # Collapse 3+ consecutive newlines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Collapse horizontal whitespace within a line
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()
