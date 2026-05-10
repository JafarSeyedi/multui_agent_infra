# engines/document/ingestion/utils/hashing.py
from __future__ import annotations

import hashlib


def sha256_bytes(data: bytes) -> str:
    """
    Deterministic SHA-256 hash for raw bytes.
    """
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def sha256_text(text: str, encoding: str = "utf-8") -> str:
    """
    SHA-256 over a UTF-8 encoded string.
    """
    return sha256_bytes(text.encode(encoding))


def combined_hash(*values: str | None) -> str:
    """
    Combines multiple string fragments into one stable hash.
    Useful for (document_id + chunk_id + version) style operations.
    """
    h = hashlib.sha256()
    for v in values:
        if v:
            h.update(v.encode("utf-8"))
    return h.hexdigest()
