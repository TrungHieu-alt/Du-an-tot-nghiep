"""LLM parser adapter boundary.

Per `docs/mvp-roadmap/provider-strategy.md` Slice 6: structured parsing lives
behind a narrow interface so production providers can be swapped without
changing the worker. The default mode is a deterministic local parser; an
OpenAI-compatible provider is enabled via env vars.

Contract:
- `parse_resume(text, filename)` returns a `ParsedResume`.
- `parse_job(text, filename)` returns a `ParsedJob`.
- All enum fields on the output MUST be canonical values (validated by
  the adapter before returning). Adapters must NEVER return raw provider
  output unsanitized.
- `parser_version` is a stable string persisted onto `parse_jobs.parser_version`
  for diagnosis/backfill.
- Recoverable provider errors raise `ParserError`; the worker marks the parse
  job `failed` and preserves the original file.
"""
from __future__ import annotations

from typing import Protocol

from jobconnect.modules.documents.local_parser import ParsedJob, ParsedResume


class ParserError(Exception):
    """Raised by an LLM adapter when structured parsing cannot complete.

    The worker catches this and marks the parse job `failed` with the message
    surfaced through `parse_jobs.error_message`. The original file is preserved.
    """


class LLMParser(Protocol):
    """Adapter interface for structured CV/JD parsing."""

    parser_version: str

    def parse_resume(self, text: str, filename: str = "") -> ParsedResume:
        """Map preprocessed CV text into canonical resume fields."""

    def parse_job(self, text: str, filename: str = "") -> ParsedJob:
        """Map preprocessed JD text into canonical job fields."""
