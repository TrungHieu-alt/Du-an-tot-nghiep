"""Local text preprocessing for normal CV/JD extraction flows."""

from __future__ import annotations

import re
import unicodedata
from typing import Any


BAD_ENCODING_CHARS = {"\x00", "\ufffd"}
BULLET_TRANSLATION = str.maketrans(
    {
        "•": "-",
        "▪": "-",
        "●": "-",
        "◦": "-",
        "–": "-",
        "—": "-",
    }
)

MIN_USABLE_CHARS = 40
MIN_LETTER_RATIO = 0.35
MAX_BAD_CHAR_RATIO = 0.02


def _is_removable_control(char: str) -> bool:
    if char in {"\n", "\t"}:
        return False
    return unicodedata.category(char).startswith("C")


def preprocess_text(raw_text: str) -> str:
    """Normalize extracted document text before rule-based parsing."""

    text = unicodedata.normalize("NFC", raw_text or "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.translate(BULLET_TRANSLATION)
    text = "".join(char for char in text if char not in BAD_ENCODING_CHARS)
    text = "".join(char for char in text if not _is_removable_control(char))
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"[ \t]*\n[ \t]*", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def analyze_text_quality(text: str) -> dict[str, Any]:
    """Return deterministic quality signals for extracted document text."""

    raw_text = text or ""
    cleaned = preprocess_text(raw_text)
    length = len(cleaned)
    raw_length = len(raw_text)
    letter_count = sum(1 for char in cleaned if char.isalpha())
    visible_count = sum(1 for char in cleaned if not char.isspace())
    letter_ratio = letter_count / visible_count if visible_count else 0.0
    bad_count = sum(
        1
        for char in raw_text
        if char in BAD_ENCODING_CHARS or _is_removable_control(char)
    )
    bad_char_ratio = bad_count / raw_length if raw_length else 0.0

    warnings: list[str] = []
    if not cleaned:
        warnings.append("empty_text")
    elif length < MIN_USABLE_CHARS:
        warnings.append("text_too_short")
    if cleaned and letter_ratio < MIN_LETTER_RATIO:
        warnings.append("too_many_non_letter_characters")
    if bad_char_ratio > MAX_BAD_CHAR_RATIO:
        warnings.append("too_many_bad_encoding_characters")

    return {
        "is_usable": not warnings,
        "length": length,
        "letter_ratio": round(letter_ratio, 4),
        "bad_char_ratio": round(bad_char_ratio, 4),
        "warnings": warnings,
    }


def _split_long_segment(segment: str, max_chars: int) -> list[str]:
    chunks: list[str] = []
    current = ""
    for word in segment.split():
        if len(word) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(word[index:index + max_chars] for index in range(0, len(word), max_chars))
            continue
        candidate = f"{current} {word}".strip()
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = word
    if current:
        chunks.append(current)
    return chunks


def split_text_into_chunks(text: str, max_chars: int = 1200) -> list[str]:
    """Split cleaned text into parser-friendly chunks."""

    if max_chars <= 0:
        raise ValueError("max_chars must be positive")

    cleaned = preprocess_text(text)
    if not cleaned:
        return []

    chunks: list[str] = []
    current = ""
    segments = re.split(r"\n{2,}", cleaned)
    for segment in segments:
        segment = segment.strip()
        if not segment:
            continue
        segment_parts = [segment] if len(segment) <= max_chars else _split_long_segment(segment, max_chars)
        for part in segment_parts:
            candidate = f"{current}\n\n{part}".strip() if current else part
            if len(candidate) <= max_chars:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                current = part
    if current:
        chunks.append(current)
    return chunks
