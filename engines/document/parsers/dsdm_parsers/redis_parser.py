# engines/document/parsers/dsdm_parsers/redis_parser.py
"""Redis parser (live key scanning)."""
from .base_dsdm_parser import BaseDSDMParser, DSDMParseOptions
from .dsdm_utils import scalar_value
from ...models.dsdm_models import DataNode, DataNodeKind, DataDocument, DataValue
from ...models.msdm_models import Entity, ScalarType
from ...models.media_types import MEDIA_TYPES


class RedisParser(BaseDSDMParser):
    name = "redis"

    async def _parse_to_datanode(self, raw_bytes: bytes, options: DSDMParseOptions) -> DataNode:
        raise NotImplementedError("Use fetch_from_redis for live Redis data")

    def _detect_media_type(self, source_name: str) -> str:
        return "application/x-redis-data"

    async def fetch_from_redis(
        self,
        redis_client,
        pattern: str = "*",
        count: int = 100,
        entity: Entity | None = None,
        options: DSDMParseOptions | None = None,
    ) -> DataDocument:
        entity = entity or (options.msdm_schema.entities[0] if options and options.msdm_schema and options.msdm_schema.entities else None)

        keys = []
        async for key in redis_client.scan_iter(match=pattern, count=count):
            keys.append(key)
        values = await redis_client.mget(keys)

        obj_node = DataNode(node_id="node:$", kind=DataNodeKind.OBJECT, path="$", name="redis_data")
        for key, val in zip(keys, values):
            key_str = key.decode() if isinstance(key, bytes) else key
            raw_val = val.decode() if isinstance(val, bytes) else val

            if entity and entity.attributes:
                attr = entity.attributes[0]
                value = self._coerce_redis_value(raw_val, attr)
            else:
                value = scalar_value(raw_val)

            obj_node.children.append(DataNode(
                node_id=f"node:$.{key_str}",
                kind=DataNodeKind.SCALAR,
                path=f"$.{key_str}",
                name=key_str,
                value=value,
            ))

        media_type = MEDIA_TYPES.get("application/x-redis-data", MEDIA_TYPES["binary"])
        doc = DataDocument(
            title="Redis key‑value snapshot",
            document_id="redis:snapshot",
            media_type=media_type,
            root=obj_node,
        )
        if options and options.msdm_schema and entity:
            self._bind_schema(doc, options.msdm_schema, options.inject_defaults, options.validate_against_schema)
        return doc

    def _coerce_redis_value(self, raw: str | None, attr) -> DataValue | None:
        if raw is None:
            if attr.default_value is not None:
                return self._coerce_default_value(attr)
            return None
        dt = attr.data_type.base
        try:
            if dt == ScalarType.INT:
                return DataValue(scalar_type=ScalarType.INT, value=int(raw), lexical_value=raw)
            if dt == ScalarType.FLOAT:
                return DataValue(scalar_type=ScalarType.FLOAT, value=float(raw), lexical_value=raw)
            if dt == ScalarType.BOOLEAN:
                val = raw.lower() in ('true', '1', 'yes')
                return DataValue(scalar_type=ScalarType.BOOLEAN, value=val, lexical_value=raw)
            return scalar_value(raw)
        except Exception:
            return scalar_value(raw)

    # _coerce_default_value is inherited from BaseDSDMParser