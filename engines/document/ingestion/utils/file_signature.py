# engines/document/ingestion/utils/file_signature.py
from __future__ import annotations

import hashlib


def file_signature(data: bytes, sample_size: int = 4096) -> str:
    """
    Fast, partial signature of the file (first + last N bytes):
    Useful for dedupe, identity, version detection.
    Not cryptographically strong but extremely fast.
    """

    if len(data) <= sample_size * 2:
        # small files → normal SHA256
        h1 = hashlib.sha256()
        h1.update(data)
        return h1.hexdigest()

    head = data[:sample_size]
    tail = data[-sample_size:]

    h = hashlib.blake2b(digest_size=32)
    h.update(head)
    h.update(tail)
    h.update(len(data).to_bytes(8, "big"))

    return h.hexdigest()
