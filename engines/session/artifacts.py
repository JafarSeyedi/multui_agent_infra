from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ArtifactPart:
    data: bytes
    mime_type: str = "application/octet-stream"


class BaseArtifactService(ABC):
    @abstractmethod
    async def save_artifact(
        self, app_name: str, user_id: str, session_id: str,
        filename: str, data: bytes, mime_type: str,
    ) -> int:
        ...

    @abstractmethod
    async def load_artifact(
        self, app_name: str, user_id: str, session_id: str,
        filename: str, version: int | None = None,
    ) -> ArtifactPart | None:
        ...

    @abstractmethod
    async def list_artifact_keys(
        self, app_name: str, user_id: str, session_id: str,
    ) -> list[str]:
        ...

    @abstractmethod
    async def delete_artifact(
        self, app_name: str, user_id: str, session_id: str,
        filename: str,
    ) -> None:
        ...


class InMemoryArtifactService(BaseArtifactService):
    def __init__(self) -> None:
        self._store: dict[str, list[ArtifactPart]] = {}

    def _key(
        self, app_name: str, user_id: str, session_id: str, filename: str,
    ) -> str:
        return f"{app_name}:{user_id}:{session_id}:{filename}"

    async def save_artifact(
        self, app_name: str, user_id: str, session_id: str,
        filename: str, data: bytes, mime_type: str,
    ) -> int:
        key = self._key(app_name, user_id, session_id, filename)
        if key not in self._store:
            self._store[key] = []
        self._store[key].append(ArtifactPart(data=data, mime_type=mime_type))
        return len(self._store[key]) - 1

    async def load_artifact(
        self, app_name: str, user_id: str, session_id: str,
        filename: str, version: int | None = None,
    ) -> ArtifactPart | None:
        key = self._key(app_name, user_id, session_id, filename)
        versions = self._store.get(key)
        if not versions:
            return None
        if version is None:
            return versions[-1]
        if 0 <= version < len(versions):
            return versions[version]
        return None

    async def list_artifact_keys(
        self, app_name: str, user_id: str, session_id: str,
    ) -> list[str]:
        prefix = f"{app_name}:{user_id}:{session_id}:"
        return [
            k.split(":")[3] for k in self._store
            if k.startswith(prefix)
        ]

    async def delete_artifact(
        self, app_name: str, user_id: str, session_id: str,
        filename: str,
    ) -> None:
        key = self._key(app_name, user_id, session_id, filename)
        self._store.pop(key, None)
