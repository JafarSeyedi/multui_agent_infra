from __future__ import annotations

from datetime import datetime

from ..base import LogStorage
from engines.storage.relational.base import SQLStorage


class SqlLogStorage(LogStorage):
    """Async log persistence layer built on top of SQLStorage."""

    def __init__(self, sql_storage: SQLStorage) -> None:
        super().__init__()
        self.sql = sql_storage

    async def connect(self) -> None:
        await self.sql.connect()
        self._connected = True

    async def disconnect(self) -> None:
        await self.sql.disconnect()
        self._connected = False

    async def health(self) -> bool:
        return await self.sql.health()

    async def log_agent_execution(self, agent_name: str, record: dict) -> None:
        timestamp = record.get("timestamp", datetime.utcnow().isoformat())
        key = f"exec:{agent_name}:{timestamp}"
        await self.sql.save(key, record)

    async def list_agent_logs(self, agent_name: str) -> list[str]:
        return await self.sql.list_keys(prefix=f"exec:{agent_name}:")

    async def get_agent_log(self, key: str) -> dict | None:
        return await self.sql.load(key)

    async def log_event(self, event_type: str, payload: dict) -> None:
        key = f"event:{event_type}:{datetime.utcnow().isoformat()}"
        await self.sql.save(key, payload)

    async def list_events(self, event_type: str | None = None) -> list[str]:
        prefix = f"event:{event_type}:" if event_type else "event:"
        return await self.sql.list_keys(prefix=prefix)

    async def get_event(self, key: str) -> dict | None:
        return await self.sql.load(key)
