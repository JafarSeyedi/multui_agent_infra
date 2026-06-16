# engines/artifacts/backends/in_memory/in_memory_artifacts.py
from __future__ import annotations

import uuid
from typing import Optional

from ...models.artifacts_models import Artifact
from ...plugin import IArtifactStore, IArtifactVersioner


class InMemoryArtifactStore(IArtifactStore):
    name = "in_memory"

    def __init__(self) -> None:
        self._store: dict[str, Artifact] = {}

    async def store(self, name: str, data: bytes, metadata: dict | None = None) -> str:
        artifact_id = str(uuid.uuid4())
        self._store[artifact_id] = Artifact(
            artifact_id=artifact_id, name=name, data=data, metadata=metadata or {}
        )
        return artifact_id

    async def retrieve(self, artifact_id: str) -> Optional[bytes]:
        art = self._store.get(artifact_id)
        return art.data if art else None

    async def delete(self, artifact_id: str) -> None:
        self._store.pop(artifact_id, None)


class InMemoryArtifactVersioner(IArtifactVersioner):
    name = "in_memory"

    def __init__(self) -> None:
        self._versions: dict[str, dict[int, bytes]] = {}

    async def create_version(self, artifact_id: str, data: bytes) -> int:
        if artifact_id not in self._versions:
            self._versions[artifact_id] = {}
        next_ver = len(self._versions[artifact_id]) + 1
        self._versions[artifact_id][next_ver] = data
        return next_ver

    async def get_version(self, artifact_id: str, version: int) -> Optional[bytes]:
        versions = self._versions.get(artifact_id)
        if versions is None:
            return None
        return versions.get(version)
