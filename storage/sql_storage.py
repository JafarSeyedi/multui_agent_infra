import json
import sqlite3
from typing import Dict, Any, Optional
from .base_storage import StorageAdapter


class SQLStorage(StorageAdapter):
    """Simple SQL-based storage adapter (SQLite or similar)."""

    def __init__(self, db_path: str = "database.db"):
        self.conn = sqlite3.connect(db_path)
        self._create_table()

    def _create_table(self):
        with self.conn:
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS kv_store (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
                """
            )

    def save(self, key: str, data: Dict[str, Any]) -> None:
        serialized = json.dumps(data)
        with self.conn:
            self.conn.execute(
                "INSERT OR REPLACE INTO kv_store (key, value) VALUES (?, ?)",
                (key, serialized),
            )

    def load(self, key: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.execute("SELECT value FROM kv_store WHERE key=?", (key,))
        row = cursor.fetchone()
        return json.loads(row[0]) if row else None

    def delete(self, key: str) -> None:
        with self.conn:
            self.conn.execute("DELETE FROM kv_store WHERE key=?", (key,))

    def list_keys(self, prefix: Optional[str] = None) -> list[str]:
        query = "SELECT key FROM kv_store"
        if prefix:
            query += " WHERE key LIKE ?"
            cursor = self.conn.execute(query, (f"{prefix}%",))
        else:
            cursor = self.conn.execute(query)
        return [row[0] for row in cursor.fetchall()]
