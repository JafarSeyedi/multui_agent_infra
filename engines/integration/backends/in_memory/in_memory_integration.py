# engines/integration/backends/in_memory/in_memory_integration.py
from __future__ import annotations

from typing import Any

from ...models.integration_models import SyncResult
from ...plugin import IConnector, ITransformer, ISyncEngine


class InMemoryConnector(IConnector):
    name = "in_memory"

    def __init__(self) -> None:
        self._connected = False
        self._sent: list[dict[str, Any]] = []

    async def connect(self, config: dict[str, Any]) -> bool:
        self._connected = True
        return True

    async def send(self, payload: dict[str, Any]) -> dict[str, Any]:
        self._sent.append(payload)
        return {"status": "sent", "payload": payload}


class InMemoryTransformer(ITransformer):
    name = "in_memory"

    async def transform(self, data: dict[str, Any], mapping: dict[str, str]) -> dict[str, Any]:
        result = {}
        for target_field, source_field in mapping.items():
            result[target_field] = data.get(source_field)
        return result


class InMemorySyncEngine(ISyncEngine):
    name = "in_memory"

    def __init__(self) -> None:
        self._synced: list[dict[str, Any]] = []

    async def sync(self, source: str, target: str, items: list[dict[str, Any]]) -> dict[str, Any]:
        self._synced.extend(items)
        return {"success_count": len(items), "failure_count": 0, "errors": []}
