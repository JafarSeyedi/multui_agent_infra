# engines/document/writers/dsdm_writers/redis_writer.py
"""Redis writer with connection management."""
from __future__ import annotations

import json
from typing import Any

from ...models.dsdm_models import DataDocument, DataNode, DataNodeKind
from .base_dsdm_writer import BaseDSDMWriter, DSDMWriteOptions
from .json_writer import JSONWriter


class RedisWriter(BaseDSDMWriter):
    name = "redis"

    def get_supported_media_types(self) -> list[str]:
        return ["application/x-redis-data"]

    def get_supported_extensions(self) -> list[str]:
        return []

    async def _serialise_root(self, root_node: DataNode, options: DSDMWriteOptions) -> bytes:
        # Output as JSON for file dump
        writer = JSONWriter()
        return await writer._serialise_root(root_node, options)

    async def _serialise_node(self, node: DataNode, options: DSDMWriteOptions) -> bytes:
        return await self._serialise_root(node, options)

    async def write_to_redis(
        self,
        doc: DataDocument,
        redis_client,           # redis.asyncio.Redis
        options: DSDMWriteOptions | None = None,
    ) -> None:
        root = doc.root
        if root.kind == DataNodeKind.OBJECT:
            for child in root.children:
                key = child.name
                if key is None:
                    continue
                value = self._extract_redis_value(child)
                if isinstance(value, (dict, list)):
                    await redis_client.set(key, json.dumps(value))
                else:
                    await redis_client.set(key, value)
        else:
            raise ValueError("Redis writer expects root OBJECT of key-value pairs")

    def _extract_redis_value(self, node: DataNode) -> Any:
        if node.kind == DataNodeKind.OBJECT:
            return {c.name: self._extract_redis_value(c) for c in node.children if c.name is not None}
        if node.kind == DataNodeKind.ARRAY:
            return [self._extract_redis_value(c) for c in node.children]
        if node.value:
            return node.value.value
        return None