# engines/document/ingestion/ingestion_utils.py

from __future__ import annotations

import hashlib
from typing import Optional


class IngestionUtils:
    """
    Helper utilities for hashing, naming keys, and file metadata processing.
    """

    @staticmethod
    def compute_sha256(data: bytes) -> str:
        h = hashlib.sha256()
        h.update(data)
        return h.hexdigest()

    @staticmethod
    def guess_extension(filename: str) -> Optional[str]:
        if "." not in filename:
            return None
        return filename.lower().rsplit(".", 1)[-1]

    @staticmethod
    def make_object_key(document_id: str, filename: str) -> str:
        return f"{document_id}/{filename}"
