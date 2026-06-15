from __future__ import annotations

import tempfile

import pytest

from engines.storage.relational.implementors import BridgeRelationalStorage
from engines.storage.relational.implementors import RelationalImplementor
from engines.storage.relational.implementors import SQLAlchemyImplementor
from engines.storage.relational.implementors import SQLiteImplementor


class TestBridgeRelationalStorage:
    async def test_sqlite_lifecycle(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            impl = SQLiteImplementor(tmp.name)
            storage = BridgeRelationalStorage(impl)

            assert await storage.health() is False
            await storage.connect()
            assert await storage.health() is True
            await storage.disconnect()
            assert await storage.health() is False

    async def test_sqlite_execute_and_fetch(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            impl = SQLiteImplementor(tmp.name)
            storage = BridgeRelationalStorage(impl)
            await storage.connect()

            await storage.execute("CREATE TABLE test (id INTEGER, name TEXT)")
            await storage.execute("INSERT INTO test (id, name) VALUES (:id, :name)", {"id": 1, "name": "Alice"})
            await storage.execute("INSERT INTO test (id, name) VALUES (:id, :name)", {"id": 2, "name": "Bob"})

            row = await storage.fetch_one("SELECT * FROM test WHERE id = :id", {"id": 1})
            assert row is not None
            assert row["name"] == "Alice"

            rows = await storage.fetch_all("SELECT * FROM test ORDER BY id")
            assert len(rows) == 2
            assert rows[0]["name"] == "Alice"
            assert rows[1]["name"] == "Bob"

    async def test_fetch_one_none(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            impl = SQLiteImplementor(tmp.name)
            storage = BridgeRelationalStorage(impl)
            await storage.connect()
            await storage.execute("CREATE TABLE t (k TEXT)")
            row = await storage.fetch_one("SELECT * FROM t WHERE k = :k", {"k": "x"})
            assert row is None

    async def test_type_hierarchy(self) -> None:
        impl = SQLiteImplementor(":memory:")
        assert isinstance(impl, RelationalImplementor)
