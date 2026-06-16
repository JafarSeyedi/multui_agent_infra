# engines/artifacts/plugin.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class IArtifactStore(ABC):
    name: str = "base"

    @abstractmethod
    async def store(self, name: str, data: bytes, metadata: dict | None = None) -> str: ...

    @abstractmethod
    async def retrieve(self, artifact_id: str) -> Optional[bytes]: ...

    @abstractmethod
    async def delete(self, artifact_id: str) -> None: ...


class IArtifactVersioner(ABC):
    name: str = "base"

    @abstractmethod
    async def create_version(self, artifact_id: str, data: bytes) -> int: ...

    @abstractmethod
    async def get_version(self, artifact_id: str, version: int) -> Optional[bytes]: ...
