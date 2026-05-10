# engines/document/parsers/dsdm_parsers/cassandra_parser.py
"""Cassandra data parser."""
from __future__ import annotations

from .base_dsdm_parser import BaseDSDMParser, DSDMParseOptions
from ...models.dsdm_models import DataDocument, DataNode, DataNodeKind, DataValue
from ...models.msdm_models import Entity, ScalarType
from ...models.media_types import MEDIA_TYPES


class CassandraParser(BaseDSDMParser):
    name = "cassandra"

    async def fetch_from_cassandra(
        self,
        session,
        keyspace: str,
        entity: Entity | None = None,
        query_override: str | None = None,
        options: DSDMParseOptions | None = None,
    ) -> DataDocument:
        entity = entity or (options.msdm_schema.entities[0] if options and options.msdm_schema and options.msdm_schema.entities else None)
        if entity is None:
            raise ValueError("Entity must be provided or present in options.msdm_schema")

        if query_override:
            query = query_override
        else:
            cols = [attr.name for attr in entity.attributes]
            query = f"SELECT {', '.join(cols)} FROM {keyspace}.{entity.name}"
        result_set = await session.execute_async(query)
        rows = list(result_set)

        array_node = DataNode(node_id="node:$", kind=DataNodeKind.ARRAY, path="$", name=entity.name)
        for idx, row in enumerate(rows):
            obj = DataNode(node_id=f"node:$[{idx}]", kind=DataNodeKind.OBJECT,
                           path=f"$[{idx}]", name=str(idx))
            for attr in entity.attributes:
                raw = getattr(row, attr.name, None) if hasattr(row, attr.name) else None
                value = self._coerce_cassandra_value(raw, attr)
                if value is None and attr.required:
                    obj.metadata["_required_missing"] = True
                obj.children.append(DataNode(
                    node_id=f"node:$[{idx}].{attr.name}",
                    kind=DataNodeKind.SCALAR,
                    path=f"$[{idx}].{attr.name}",
                    name=attr.name,
                    value=value,
                ))
            array_node.children.append(obj)

        media_type = MEDIA_TYPES.get("application/x-cassandra-rows", MEDIA_TYPES["binary"])
        doc = DataDocument(
            title=f"Cassandra rows from {entity.name}",
            document_id=f"cass:{keyspace}.{entity.name}",
            media_type=media_type,
            root=array_node,
        )
        if options and options.msdm_schema:
            self._bind_schema(doc, options.msdm_schema, options.inject_defaults, options.validate_against_schema)
        return doc

    def _coerce_cassandra_value(self, raw, attr) -> DataValue | None:
        if raw is None:
            if attr.default_value is not None:
                return self._coerce_default_value(attr)
            return None
        dt = attr.data_type.base
        try:
            if dt in (ScalarType.INT, ScalarType.LONG):
                return DataValue(scalar_type=ScalarType.INT, value=int(raw), lexical_value=str(raw))
            if dt == ScalarType.FLOAT or dt == ScalarType.DOUBLE:
                return DataValue(scalar_type=ScalarType.FLOAT, value=float(raw), lexical_value=str(raw))
            return DataValue(scalar_type=ScalarType.STRING, value=str(raw), lexical_value=str(raw))
        except Exception:
            return DataValue(scalar_type=ScalarType.STRING, value=str(raw), lexical_value=str(raw))

    # helper _coerce_default_value is inherited from base parser