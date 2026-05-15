"""Local filesystem implementation of the Storage protocol.

Used for dev/test runtimes. Production deployments swap this for a cloud
adapter matching the same protocol (S3/MinIO). The download URL scheme
``local://<object_key>`` is intentionally non-HTTP: it signals that the file
is on the application volume and must be read through a future server-side
download proxy rather than a public link.
"""
from __future__ import annotations

import os
import secrets
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import BinaryIO

from .base import DownloadLink, StoredObject


_MIME_TO_EXT: dict[str, str] = {
    "application/pdf": "pdf",
    "application/msword": "doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
}


def _safe_extension(mime: str, fallback_filename: str) -> str:
    ext = _MIME_TO_EXT.get(mime)
    if ext:
        return ext
    suffix = Path(fallback_filename).suffix.lstrip(".").lower()
    return suffix or "bin"


class LocalFilesystemStorage:
    """Write files under ``{root}/documents/`` using a random key."""

    def __init__(self, root: str | os.PathLike[str]) -> None:
        self._root = Path(root)
        self._documents_dir = self._root / "documents"
        self._documents_dir.mkdir(parents=True, exist_ok=True)

    # Storage protocol -------------------------------------------------

    def save(
        self,
        stream: BinaryIO,
        *,
        key_hint: str,
        content_type: str,
        max_bytes: int,
    ) -> StoredObject:
        ext = _safe_extension(content_type, key_hint)
        object_key = f"documents/{secrets.token_urlsafe(16)}.{ext}"
        target = self._root / object_key
        target.parent.mkdir(parents=True, exist_ok=True)
        written = 0
        # Stream in chunks so we can short-circuit oversize uploads.
        with target.open("wb") as fh:
            while True:
                chunk = stream.read(64 * 1024)
                if not chunk:
                    break
                written += len(chunk)
                if written > max_bytes:
                    fh.close()
                    target.unlink(missing_ok=True)
                    raise ValueError(
                        f"Upload exceeds maximum size of {max_bytes} bytes."
                    )
                fh.write(chunk)
        return StoredObject(object_key=object_key, size_bytes=written)

    def download_url(self, object_key: str, ttl_seconds: int = 900) -> DownloadLink:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
        return DownloadLink(
            download_url=f"local://{object_key}",
            expires_at=expires_at.isoformat(),
        )

    def exists(self, object_key: str) -> bool:
        return (self._root / object_key).is_file()

    # Test helpers -----------------------------------------------------

    def absolute_path(self, object_key: str) -> Path:
        return self._root / object_key

    def reset(self) -> None:
        """Wipe and recreate the documents directory. For tests only."""
        if self._documents_dir.exists():
            shutil.rmtree(self._documents_dir)
        self._documents_dir.mkdir(parents=True, exist_ok=True)
