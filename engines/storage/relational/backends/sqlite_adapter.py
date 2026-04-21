from __future__ import annotations

import aiosqlite
from typing import Any, Dict, List, Optional, Sequence

from ..base import RelationalStorage


class SQLiteStorageAdapter(RelationalStorage):
    """Async SQLite relational backend."""

    def __init__(self, db_path: str = "database.db") -> None:
        super().__init__()
        self.db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        self._connection = await aiosqlite.connect(self.db_path)
        self._connection.row_factory = aiosqlite.Row
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

    def _normalize_params(self, params: Optional[Dict[str, Any]]) -> Sequence[Any] | Dict[str, Any]:
        return params or {}

    async def execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> None:
        await self.ensure_connected()
        if self._connection is None:
            raise RuntimeError("SQLite connection is not initialized.")
        await self._connection.execute(query, self._normalize_params(params))
        await self._connection.commit()

    async def fetch_one(self, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        await self.ensure_connected()
        if self._connection is None:
            raise RuntimeError("SQLite connection is not initialized.")
        cursor = await self._connection.execute(query, self._normalize_params(params))
        row = await cursor.fetchone()
        return dict(row) if row is not None else None

    async def fetch_all(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        await self.ensure_connected()
        if self._connection is None:
            raise RuntimeError("SQLite connection is not initialized.")
        cursor = await self._connection.execute(query, self._normalize_params(params))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
