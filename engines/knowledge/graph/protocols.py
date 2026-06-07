from __future__ import annotations

from typing import Any, Protocol


class EntityExtractorProtocol(Protocol):
    async def extract(self, chunks: list[Any]) -> list[Any]: ...


class GraphEngineProtocol(Protocol):
    entity_extractor: EntityExtractorProtocol
