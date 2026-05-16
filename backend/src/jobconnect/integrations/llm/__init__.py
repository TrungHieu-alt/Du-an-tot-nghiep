"""LLM parser adapter selection.

Runtime selects an implementation via the `LLM_PROVIDER` env var:
- `local` (default) → deterministic keyword parser (Slice 5 fallback).
- `openai`         → OpenAI-compatible chat completions; requires `OPENAI_API_KEY`.

If `LLM_PROVIDER=openai` is requested but `OPENAI_API_KEY` is missing, the
factory logs a warning and falls back to local so dev/test environments stay
runnable without provider credentials (per provider-strategy.md).
"""
from __future__ import annotations

import logging
import os
from functools import lru_cache

from .base import LLMParser, ParserError
from .local import LocalDeterministicParser
from .openai import OpenAIParser

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_parser() -> LLMParser:
    provider = os.getenv("LLM_PROVIDER", "local").lower()
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            logger.warning(
                "LLM_PROVIDER=openai but OPENAI_API_KEY missing; falling back to local parser."
            )
            return LocalDeterministicParser()
        return OpenAIParser(api_key=api_key)
    if provider != "local":
        logger.warning("Unknown LLM_PROVIDER=%r; falling back to local parser.", provider)
    return LocalDeterministicParser()


def reset_parser_cache() -> None:
    """Test helper: clear the cached adapter so env overrides take effect."""
    get_parser.cache_clear()


__all__ = [
    "LLMParser",
    "ParserError",
    "LocalDeterministicParser",
    "OpenAIParser",
    "get_parser",
    "reset_parser_cache",
]
