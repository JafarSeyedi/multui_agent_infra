from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

from ..base import ObjectStorage


class LocalFileAdapter(ObjectStorage):
    """Local filesystem object storage backend."""

    def __init__(self, base_path: str = "./data/storage") -> None:
        super().__init__()
        self.base_path = Path(base_path)

    async def connect(self) -> None:
        await asyncio.to_thread(self.base_path.mkdir, parents=True, exist_ok=True)
        self._connected = True

    async def disconnect(self) -> None:
        self._connected = False

    async def health(self) -> bool:
        return self.base_path.exists() and self.base_path.is_dir()

    def _get_path(self, key: str) -> Path:
        return self.base_path / key

    async def put(self, key: str, data: bytes, content_type: Optional[str] = None) -> None:
        await self.ensure_connected()
        file_path = self._get_path(key)
        await asyncio.to_thread(file_path.parent.mkdir, parents=True, exist_ok=True)
        await asyncio.to_thread(file_path.write_bytes, data)

    async def get(self, key: str) -> bytes:
        file_path = self._get_path(key)
        if not file_path.exists():
            raise FileNotFoundError(key)
        return await asyncio.to_thread(file_path.read_bytes)

    async def delete(self, key: str) -> None:
        file_path = self._get_path(key)
        if file_path.exists():
            await asyncio.to_thread(file_path.unlink)

    async def exists(self, key: str) -> bool:
        return self._get_path(key).exists()

    async def generate_url(self, key: str) -> Optional[str]:
        if not await self.exists(key):
            return None
        return str(self._get_path(key).resolve())
