from __future__ import annotations

from typing import Any
from typing import TYPE_CHECKING

from ..base import RelationalStorage

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine


class PostgresStorageAdapter(RelationalStorage):
    """Async PostgreSQL backend using SQLAlchemy's async engine."""

    def __init__(self, dsn: str) -> None:
        super().__init__()
        self.dsn = dsn
        self._engine: AsyncEngine | None = None

    async def connect(self) -> None:
        try:
            from sqlalchemy.ext.asyncio import create_async_engine
        except ImportError as exc:
            raise RuntimeError("sqlalchemy[asyncio] is required for PostgresStorageAdapter.") from exc

        self._engine = create_async_engine(self.dsn, future=True)
        self._connected = True

    async def disconnect(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()

        self._engine = None
        self._connected = False

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

        assert self._engine is not None

        from sqlalchemy import text

        async with self._engine.begin() as conn:
            await conn.execute(text(query), params or {})

    async def fetch_one(self, query: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
        if self._engine is None:
            await self.connect()

        assert self._engine is not None

        from sqlalchemy import text

        async with self._engine.connect() as conn:
            result = await conn.execute(text(query), params or {})
            row = result.mappings().first()

            return dict(row) if row is not None else None

    async def fetch_all(self, query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        if self._engine is None:
            await self.connect()

        assert self._engine is not None

        from sqlalchemy import text

        async with self._engine.connect() as conn:
            result = await conn.execute(text(query), params or {})

            return [dict(row) for row in result.mappings().all()]
