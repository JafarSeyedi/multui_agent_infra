import json
from typing import Any, Dict, List, Optional
from .connection import RedisManager
from ...base_storage import StorageAdapter

class RedisStorageAdapter(StorageAdapter):
    def __init__(self, manager: RedisManager, namespace: str = "tutor"):
        self.manager = manager
        self.namespace = namespace

    def _get_key(self, key: str) -> str:
        return f"{self.namespace}:{key}"

    async def save(self, key: str, data: Dict[str, Any], ttl: Optional[int] = None) -> None:
        client = await self.manager.get_client()
        full_key = self._get_key(key)
        await client.set(full_key, json.dumps(data), ex=ttl)

    async def load(self, key: str) -> Optional[Dict[str, Any]]:
        client = await self.manager.get_client()
        data = await client.get(self._get_key(key))
        return json.loads(data) if data else None

    async def delete(self, key: str) -> None:
        client = await self.manager.get_client()
        await client.delete(self._get_key(key))

    async def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        client = await self.manager.get_client()
        pattern = f"{self.namespace}:{prefix if prefix else ''}*"
        keys = await client.keys(pattern)
        # Strip namespace from returned keys
        return [k.replace(f"{self.namespace}:", "") for k in keys]
