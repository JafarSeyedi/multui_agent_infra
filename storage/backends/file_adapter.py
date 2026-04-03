import os
import json
import aiofiles
from typing import Any, Dict, List, Optional
from pathlib import Path
from ..base_storage import StorageAdapter

class LocalFileAdapter(StorageAdapter):
    """
    Local File System Storage Adapter.
    Persists data as JSON files. Ideal for local dev and backups.
    """
    def __init__(self, base_path: str = "./data/storage"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_path(self, key: str) -> Path:
        return self.base_path / f"{key}.json"

    async def save(self, key: str, data: Dict[str, Any]) -> None:
        file_path = self._get_path(key)
        async with aiofiles.open(file_path, mode='w', encoding='utf-8') as f:
            await f.write(json.dumps(data, indent=4, ensure_ascii=False))

    async def load(self, key: str) -> Optional[Dict[str, Any]]:
        file_path = self._get_path(key)
        if not file_path.exists():
            return None
        async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
            content = await f.read()
            return json.loads(content)

    async def delete(self, key: str) -> None:
        file_path = self._get_path(key)
        if file_path.exists():
            file_path.unlink()

    async def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        keys = [p.stem for p in self.base_path.glob("*.json")]
        if prefix:
            return [k for k in keys if k.startswith(prefix)]
        return keys
