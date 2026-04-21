from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..base import KeyValueStorage


class InMemoryKeyValueStorage(KeyValueStorage):
    """In-memory key-value backend for tests and local development."""

    def __init__(self) -> None:
        super().__init__()
        self._store: Dict[str, Any] = {}

    async def connect(self) -> None:
        self._connected = True

    async def disconnect(self) -> None:
        self._store.clear()
        self._connected = False

    async def health(self) -> bool:
        return True

    async def set(self, key: str, value: Any) -> None:
        self._store[key] = value

    async def get(self, key: str) -> Optional[Any]:
        return self._store.get(key)

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def exists(self, key: str) -> bool:
        return key in self._store

    async def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        keys = list(self._store.keys())
        if prefix is None:
            return keys
        return [key for key in keys if key.startswith(prefix)]
