import json
import aiosqlite
from typing import Dict, Any, Optional, List
from ..base_storage import StorageAdapter


class SQLStorage(StorageAdapter):
    """
    Async SQL-based key-value storage using SQLite.
    Suitable for logs, metadata, and lightweight persistence.
    """

    def __init__(self, db_path: str = "database.db"):
        self.db_path = db_path
        self._initialized = False

    async def _ensure_initialized(self):
        if self._initialized:
            return

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS kv_store (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
                """
            )
            await db.commit()

        self._initialized = True

    async def save(self, key: str, data: Dict[str, Any]) -> None:
        await self._ensure_initialized()

        serialized = json.dumps(data)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO kv_store (key, value) VALUES (?, ?)",
                (key, serialized),
            )
            await db.commit()

    async def load(self, key: str) -> Optional[Dict[str, Any]]:
        await self._ensure_initialized()

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT value FROM kv_store WHERE key=?",
                (key,),
            )
            row = await cursor.fetchone()

        return json.loads(row[0]) if row else None

    async def delete(self, key: str) -> None:
        await self._ensure_initialized()

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM kv_store WHERE key=?", (key,))
            await db.commit()

    async def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        await self._ensure_initialized()

        async with aiosqlite.connect(self.db_path) as db:
            if prefix:
                cursor = await db.execute(
                    "SELECT key FROM kv_store WHERE key LIKE ?",
                    (f"{prefix}%",),
                )
            else:
                cursor = await db.execute("SELECT key FROM kv_store")

            rows = await cursor.fetchall()

        return [row[0] for row in rows]
