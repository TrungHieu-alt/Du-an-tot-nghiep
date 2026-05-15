"""Storage adapter protocol shared by local-fs and future cloud backends."""
from __future__ import annotations

from dataclasses import dataclass
from typing import BinaryIO, Protocol


@dataclass(frozen=True)
class StoredObject:
    object_key: str
    size_bytes: int


@dataclass(frozen=True)
class DownloadLink:
    download_url: str
    expires_at: str  # ISO 8601 timestamp with timezone


class Storage(Protocol):
    """Minimal write/read surface for uploaded documents."""

    def save(
        self,
        stream: BinaryIO,
        *,
        key_hint: str,
        content_type: str,
        max_bytes: int,
    ) -> StoredObject:
        """Persist `stream` under a key derived from `key_hint`.

        Implementations must enforce `max_bytes` while streaming and raise
        ``ValueError`` when exceeded. They must return the actual byte count
        consumed.
        """

    def download_url(self, object_key: str, ttl_seconds: int = 900) -> DownloadLink:
        """Build a short-lived URL for retrieving the stored object."""

    def open(self, object_key: str) -> BinaryIO:
        """Open a stored object for reading. Caller is responsible for closing."""

    def exists(self, object_key: str) -> bool:
        """True if the object is reachable through this adapter."""
