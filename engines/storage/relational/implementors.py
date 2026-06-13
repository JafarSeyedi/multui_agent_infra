from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Any

from engines.storage.relational.base import RelationalStorage


class RelationalImplementor(ABC):
    """Bridge implementor — abstracts database-specific execution."""

    @abstractmethod
    async def connect(self) -> None:
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        ...

    @abstractmethod
    async def health(self) -> bool:
        ...

    @abstractmethod
    async def execute(self, query: str, params: dict[str, Any] | None = None) -> None:
        ...

    @abstractmethod
    async def fetch_one(self, query: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
        ...

    @abstractmethod
    async def fetch_all(self, query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        ...


class SQLAlchemyImplementor(RelationalImplementor):
    """Bridge implementor for SQLAlchemy-based databases (Postgres, MySQL, SQL Server)."""

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        self._engine: Any = None

    async def connect(self) -> None:
        from sqlalchemy.ext.asyncio import create_async_engine
        self._engine = create_async_engine(self.dsn, future=True)

    async def disconnect(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()
        self._engine = None

    async def health(self) -> bool:
        if self._engine is None:
            return False
        try:
            from sqlalchemy import text
            async with self._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    async def execute(self, query: str, params: dict[str, Any] | None = None) -> None:
        if self._engine is None:
            await self.connect()
        from sqlalchemy import text
        async with self._engine.begin() as conn:
            await conn.execute(text(query), params or {})

    async def fetch_one(self, query: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
        if self._engine is None:
            await self.connect()
        from sqlalchemy import text
        async with self._engine.connect() as conn:
            result = await conn.execute(text(query), params or {})
            row = result.mappings().first()
            return dict(row) if row is not None else None

    async def fetch_all(self, query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        if self._engine is None:
            await self.connect()
        from sqlalchemy import text
        async with self._engine.connect() as conn:
            result = await conn.execute(text(query), params or {})
            return [dict(row) for row in result.mappings().all()]


class SQLiteImplementor(RelationalImplementor):
    """Bridge implementor for aiosqlite-based databases."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._connection: Any = None

    async def connect(self) -> None:
        import aiosqlite
        self._connection = await aiosqlite.connect(self.db_path)
        self._connection.row_factory = aiosqlite.Row

    async def disconnect(self) -> None:
        if self._connection is not None:
            await self._connection.close()
        self._connection = None

    async def health(self) -> bool:
        if self._connection is None:
            return False
        try:
            await self._connection.execute("SELECT 1")
            return True
        except Exception:
            return False

    async def execute(self, query: str, params: dict[str, Any] | None = None) -> None:
        if self._connection is None:
            await self.connect()
        await self._connection.execute(query, params or {})
        await self._connection.commit()

    async def fetch_one(self, query: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
        if self._connection is None:
            await self.connect()
        cursor = await self._connection.execute(query, params or {})
        row = await cursor.fetchone()
        if row is None:
            return None
        return dict(row) if hasattr(row, "keys") else {str(i): v for i, v in enumerate(row)}

    async def fetch_all(self, query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        if self._connection is None:
            await self.connect()
        cursor = await self._connection.execute(query, params or {})
        rows = await cursor.fetchall()
        if not rows:
            return []
        if hasattr(rows[0], "keys"):
            return [dict(row) for row in rows]
        keys = [d[0] for d in cursor.description]
        return [dict(zip(keys, row)) for row in rows]


class BridgeRelationalStorage(RelationalStorage):
    """Abstraction side of the Bridge pattern — delegates to a RelationalImplementor."""

    def __init__(self, implementor: RelationalImplementor) -> None:
        super().__init__()
        self._impl = implementor

    async def connect(self) -> None:
        await self._impl.connect()
        self._connected = True

    async def disconnect(self) -> None:
        await self._impl.disconnect()
        self._connected = False

    async def health(self) -> bool:
        return await self._impl.health()

    async def execute(self, query: str, params: dict[str, Any] | None = None) -> None:
        await self._impl.execute(query, params)

    async def fetch_one(self, query: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
        return await self._impl.fetch_one(query, params)

    async def fetch_all(self, query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        return await self._impl.fetch_all(query, params)
