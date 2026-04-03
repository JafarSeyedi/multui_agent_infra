import redis
import json
from typing import Dict, Any, Optional
from .base_storage import StorageAdapter


class RedisStorage(StorageAdapter):

    def __init__(self, host='localhost', port=6379, db=0):
        self.client = redis.Redis(host=host, port=port, db=db)

    def save(self, key: str, data: Dict[str, Any]) -> None:
        self.client.set(key, json.dumps(data))

    def load(self, key: str) -> Optional[Dict[str, Any]]:
        value = self.client.get(key)
        return json.loads(value) if value else None

    def delete(self, key: str) -> None:
        self.client.delete(key)

    def list_keys(self, prefix: Optional[str] = None) -> list[str]:
        pattern = f"{prefix}*" if prefix else "*"
        return [k.decode() for k in self.client.keys(pattern)]

