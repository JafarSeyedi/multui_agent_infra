from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import aiosqlite

from engines.storage.base_storage import BaseStorage


class SQLStorage(BaseStorage):
    """Async SQL-backed key-value helper built on SQLite for lightweight persistence."""

    def __init__(self, db_path: str = "database.db") -> None:
        super().__init__()
        self.db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        if self._connection is None:
            self._connection = await aiosqlite.connect(self.db_path)
            await self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS kv_store (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
                """
            )
            await self._connection.commit()
        self._connected = True

    async def disconnect(self) -> None:
        if self._connection is not None:
            await self._connection.close()
        self._connection = None
        self._connected = False

    async def health(self) -> bool:
        if self._connection is None:
            return False
        try:
            await self._connection.execute("SELECT 1")
            return True
        except Exception:
            return False

    async def save(self, key: str, data: Dict[str, Any]) -> None:
        await self.ensure_connected()
        if self._connection is None:
            raise RuntimeError("SQL storage connection is not initialized.")
        await self._connection.execute(
            "INSERT OR REPLACE INTO kv_store (key, value) VALUES (?, ?)",
            (key, json.dumps(data)),
        )
        await self._connection.commit()

    async def load(self, key: str) -> Optional[Dict[str, Any]]:
        await self.ensure_connected()
        if self._connection is None:
            raise RuntimeError("SQL storage connection is not initialized.")
        cursor = await self._connection.execute("SELECT value FROM kv_store WHERE key=?", (key,))
        row = await cursor.fetchone()
        return json.loads(row[0]) if row else None

    async def delete(self, key: str) -> None:
        await self.ensure_connected()
        if self._connection is None:
            raise RuntimeError("SQL storage connection is not initialized.")
        await self._connection.execute("DELETE FROM kv_store WHERE key=?", (key,))
        await self._connection.commit()

    async def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        await self.ensure_connected()
        if self._connection is None:
            raise RuntimeError("SQL storage connection is not initialized.")
        if prefix:
            cursor = await self._connection.execute(
                "SELECT key FROM kv_store WHERE key LIKE ?",
                (f"{prefix}%",),
            )
        else:
            cursor = await self._connection.execute("SELECT key FROM kv_store")
        rows = await cursor.fetchall()
        return [row[0] for row in rows]


class RelationalStorage(BaseStorage, ABC):
    """SQL-like relational storage abstraction."""

    @abstractmethod
    async def execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> None:
        ...

    @abstractmethod
    async def fetch_one(self, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        ...

    @abstractmethod
    async def fetch_all(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        ...
