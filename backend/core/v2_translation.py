"""Optional V2-only translation helpers.

Normal CV/JD extraction must not use this module. It is only for preparing
linked V2 text from already-normalized normal Job/CV rows.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

from core.preprocess import preprocess_text, split_text_into_chunks


VIETNAMESE_CHARS = set(
    "ăâđêôơư"
    "áàảãạắằẳẵặấầẩẫậéèẻẽẹếềểễệ"
    "íìỉĩịóòỏõọốồổỗộớờởỡợ"
    "úùủũụứừửữựýỳỷỹỵ"
    "ĂÂĐÊÔƠƯ"
    "ÁÀẢÃẠẮẰẲẴẶẤẦẨẪẬÉÈẺẼẸẾỀỂỄỆ"
    "ÍÌỈĨỊÓÒỎÕỌỐỒỔỖỘỚỜỞỠỢ"
    "ÚÙỦŨỤỨỪỬỮỰÝỲỶỸỴ"
)

PROTECTED_PATTERN = re.compile(
    r"(?P<token>"
    r"https?://\S+|www\.\S+|"
    r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+|"
    r"(?:github|linkedin)\.com/\S+|"
    r"\+?\d[\d\s().-]{7,}\d"
    r")",
    flags=re.IGNORECASE,
)


@dataclass
class TranslationResult:
    text: str
    source_language: str
    warnings: list[str] = field(default_factory=list)


def translation_enabled() -> bool:
    return os.getenv("V2_TRANSLATION_ENABLED", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def detect_text_language(text: str) -> str:
    cleaned = preprocess_text(text)
    if not cleaned:
        return "unknown"

    letters = [char for char in cleaned if char.isalpha()]
    if not letters:
        return "unknown"
    vietnamese_count = sum(1 for char in letters if char in VIETNAMESE_CHARS)
    ascii_letter_count = sum(1 for char in letters if "a" <= char.lower() <= "z")

    if vietnamese_count == 0:
        return "en"
    vietnamese_ratio = vietnamese_count / max(len(letters), 1)
    if ascii_letter_count > vietnamese_count * 4 and vietnamese_ratio < 0.12:
        return "mixed"
    return "vi"


def translate_text_to_english_if_needed(text: str) -> TranslationResult:
    cleaned = preprocess_text(text)
    language = detect_text_language(cleaned)
    if not cleaned:
        return TranslationResult(text="", source_language="unknown", warnings=[])

    if not translation_enabled():
        return TranslationResult(
            text=cleaned,
            source_language=language,
            warnings=["translation_disabled"],
        )

    if language == "en":
        return TranslationResult(
            text=cleaned,
            source_language=language,
            warnings=["translation_skipped_english"],
        )

    try:
        from deep_translator import GoogleTranslator
    except Exception:
        return TranslationResult(
            text=cleaned,
            source_language=language,
            warnings=["translation_unavailable"],
        )

    translator = GoogleTranslator(source="auto", target="en")
    translated_chunks: list[str] = []
    warnings: list[str] = []
    try:
        for chunk in split_text_into_chunks(cleaned, max_chars=1200):
            masked_chunk, protected = _mask_protected_tokens(chunk)
            translated = translator.translate(masked_chunk)
            translated_chunks.append(_unmask_protected_tokens(str(translated or ""), protected))
    except Exception:
        return TranslationResult(
            text=cleaned,
            source_language=language,
            warnings=["translation_failed"],
        )

    translated_text = preprocess_text("\n\n".join(translated_chunks))
    if not translated_text:
        warnings.append("translation_failed")
        translated_text = cleaned
    return TranslationResult(
        text=translated_text,
        source_language=language,
        warnings=warnings,
    )


def _mask_protected_tokens(text: str) -> tuple[str, dict[str, str]]:
    protected: dict[str, str] = {}

    def replace(match: re.Match[str]) -> str:
        key = f"__PROTECTED_{len(protected)}__"
        protected[key] = match.group("token")
        return key

    return PROTECTED_PATTERN.sub(replace, text), protected


def _unmask_protected_tokens(text: str, protected: dict[str, str]) -> str:
    restored = text
    for key, value in protected.items():
        restored = restored.replace(key, value)
    return restored
