"""Object storage adapter boundary.

The runtime selects an implementation via ``STORAGE_BACKEND`` env var (default
``local``). Production deployments would swap in an S3/MinIO-backed adapter
matching the same :class:`Storage` protocol.
"""
from __future__ import annotations

import os
from functools import lru_cache

from .base import Storage, StoredObject, DownloadLink
from .local import LocalFilesystemStorage


@lru_cache(maxsize=1)
def get_storage() -> Storage:
    backend = os.getenv("STORAGE_BACKEND", "local").lower()
    if backend == "local":
        root = os.getenv("STORAGE_LOCAL_ROOT", "/app/backend/uploads")
        return LocalFilesystemStorage(root=root)
    raise RuntimeError(f"Unsupported STORAGE_BACKEND: {backend!r}")


def reset_storage_cache() -> None:
    """Test helper: clear the cached adapter so env overrides take effect."""
    get_storage.cache_clear()


__all__ = [
    "Storage",
    "StoredObject",
    "DownloadLink",
    "LocalFilesystemStorage",
    "get_storage",
    "reset_storage_cache",
]
