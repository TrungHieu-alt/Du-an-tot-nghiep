"""Deterministic local parser adapter (Slice 5 fallback).

Wraps `modules.documents.local_parser` behind the `LLMParser` Protocol so the
worker can swap to OpenAI without code changes. Used by default and whenever
LLM provider env vars are absent.
"""
from __future__ import annotations

from jobconnect.modules.documents.local_parser import (
    ParsedJob,
    ParsedResume,
    parse_job as _local_parse_job,
    parse_resume as _local_parse_resume,
)


class LocalDeterministicParser:
    """Slice 5 keyword-based parser, exposed via the LLMParser adapter contract."""

    parser_version: str = "local-v1"

    def parse_resume(self, text: str, filename: str = "") -> ParsedResume:
        return _local_parse_resume(text, filename=filename)

    def parse_job(self, text: str, filename: str = "") -> ParsedJob:
        return _local_parse_job(text, filename=filename)
