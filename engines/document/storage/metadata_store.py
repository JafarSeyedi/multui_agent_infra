from __future__ import annotations

from typing import Any, Dict, Optional

from engines.storage.key_value.base import KeyValueStorage


class MetadataStore:
    """Small metadata repository for parsed-document and ingestion metadata."""

    def __init__(self, storage: Optional[KeyValueStorage] = None) -> None:
        self.storage = storage
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _key(self, document_id: str) -> str:
        return f"docmeta:{document_id}"

    async def put_metadata(self, document_id: str, metadata: Dict[str, Any]) -> None:
        self._cache[document_id] = metadata
        if self.storage is not None:
            await self.storage.set(self._key(document_id), metadata)

    async def get_metadata(self, document_id: str) -> Optional[Dict[str, Any]]:
        cached = self._cache.get(document_id)
        if cached is not None:
            return cached
        if self.storage is None:
            return None
        data = await self.storage.get(self._key(document_id))
        if not isinstance(data, dict):
            return None
        self._cache[document_id] = data
        return data

    async def delete_metadata(self, document_id: str) -> None:
        self._cache.pop(document_id, None)
        if self.storage is not None:
            await self.storage.delete(self._key(document_id))
