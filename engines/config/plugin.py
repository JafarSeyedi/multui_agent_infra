# engines/config/plugin.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class IConfigSource(ABC):
    name: str = "base"

    @abstractmethod
    async def load(self) -> dict[str, Any]: ...

    @abstractmethod
    async def watch(self) -> None: ...


class ISecretResolver(ABC):
    name: str = "base"

    @abstractmethod
    async def resolve(self, secret_ref: str) -> Optional[str]: ...
