"""Runtime resource governance with scoped locks."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator, Dict


@dataclass(frozen=True)
class ResourceContext:
    name: str
    limit: int


class ResourceManager:
    """Semaphores keyed by resource name."""

    def __init__(self) -> None:
        self._sem: dict[str, asyncio.Semaphore] = {}
        self._limits: dict[str, int] = {}

    async def configure(self, name: str, limit: int) -> None:
        self._sem[name] = asyncio.Semaphore(limit)
        self._limits[name] = limit

    @asynccontextmanager
    async def acquire(self, name: str) -> AsyncIterator[ResourceContext]:
        semaphore = self._sem.setdefault(name, asyncio.Semaphore(1))
        await semaphore.acquire()
        try:
            yield ResourceContext(name=name, limit=self._limits.get(name, 1))
        finally:
            semaphore.release()

    def limit(self, name: str) -> int:
        return self._limits.get(name, 1)
