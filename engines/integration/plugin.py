# engines/integration/plugin.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class IConnector(ABC):
    name: str = "base"

    @abstractmethod
    async def connect(self, config: dict[str, Any]) -> bool: ...

    @abstractmethod
    async def send(self, payload: dict[str, Any]) -> dict[str, Any]: ...


class ITransformer(ABC):
    name: str = "base"

    @abstractmethod
    async def transform(self, data: dict[str, Any], mapping: dict[str, str]) -> dict[str, Any]: ...


class ISyncEngine(ABC):
    name: str = "base"

    @abstractmethod
    async def sync(self, source: str, target: str, items: list[dict[str, Any]]) -> dict[str, Any]: ...
