# engines/document/parsers/dsdm_parsers/sql_parser.py
"""SQL data parser."""
# Future enhancement:
#   Support streaming via AsyncDBConnection.execute_iter(query) -> AsyncIterator[dict]
#   The DSDM model currently expects a full DataNode tree, so streaming would require
#   a separate chunked DataDocument representation. This is on the roadmap.

import json
from typing import Any, Protocol, runtime_checkable
from datetime import date, datetime, time
from decimal import Decimal
import uuid
import base64

from .base_dsdm_parser import BaseDSDMParser, DSDMParseOptions
from .dsdm_utils import scalar_value
from ...models.dsdm_models import DataNode, DataNodeKind, DataDocument, DataValue
from ...models.msdm_models import Entity, ScalarType
from ...models.media_types import MEDIA_TYPES

@runtime_checkable
class AsyncDBConnection(Protocol):
    async def execute(self, query: str, params: Any = None) -> list[dict[str, Any]]:
        ...

class SQLDataParser(BaseDSDMParser):
    name = "sql_data"
    supported_extensions = (".sql_data",)

    async def _parse_to_datanode(self, raw_bytes: bytes, options: DSDMParseOptions) -> DataNode:
        rows = json.loads(raw_bytes.decode(options.encoding))
        entity = options.msdm_schema.entities[0] if options.msdm_schema and options.msdm_schema.entities else None
        return self._build_tree_from_rows(rows, entity)

    def _detect_media_type(self, source_name: str) -> str:
        return "application/vnd.sql-data+json"

    async def fetch_from_database(
        self,
        connection: AsyncDBConnection,
        entity: Entity,
        options: DSDMParseOptions,
        query_override: str | None = None,
    ) -> DataDocument:
        if query_override:
            query = query_override
        else:
            columns = [attr.name for attr in entity.attributes]
            query = f"SELECT {', '.join(columns)} FROM {entity.name}"
        rows = await connection.execute(query)
        root = self._build_tree_from_rows(rows, entity)

        media_type = MEDIA_TYPES.get("application/vnd.sql-data+json", MEDIA_TYPES["json"])
        doc = DataDocument(
            title=f"SQL result for {entity.name}",
            document_id=f"sql:{entity.name}",
            media_type=media_type,
            root=root,
        )
        if options.msdm_schema:
            self._bind_schema(doc, options.msdm_schema, options.inject_defaults, options.validate_against_schema)
        return doc

    def _build_tree_from_rows(self, rows: list[dict[str, Any]], entity: Entity | None) -> DataNode:
        array_node = DataNode(node_id="node:$", kind=DataNodeKind.ARRAY, path="$", name="rows")
        for idx, row in enumerate(rows):
            obj_node = DataNode(node_id=f"node:$[{idx}]", kind=DataNodeKind.OBJECT,
                                path=f"$[{idx}]", name=str(idx))
            if entity:
                _attr_map = {attr.name.lower(): attr for attr in entity.attributes}
                for attr in entity.attributes:
                    raw_val = row.get(attr.name) or row.get(attr.name.lower())
                    value = self._coerce_value_from_db(raw_val, attr)
                    if value is None and attr.required:
                        obj_node.metadata["_required_missing"] = True
                    obj_node.children.append(DataNode(
                        node_id=f"node:$[{idx}].{attr.name}",
                        kind=DataNodeKind.SCALAR,
                        path=f"$[{idx}].{attr.name}",
                        name=attr.name,
                        value=value,
                    ))
            else:
                for col, val in row.items():
                    obj_node.children.append(DataNode(
                        node_id=f"node:$[{idx}].{col}",
                        kind=DataNodeKind.SCALAR,
                        path=f"$[{idx}].{col}",
                        name=col,
                        value=scalar_value(val)
                    ))
            array_node.children.append(obj_node)
        return array_node

    def _coerce_value_from_db(self, raw: Any, attr) -> DataValue | None:
        if raw is None:
            if attr.default_value is not None:
                return self._parse_default(attr.default_value, attr.data_type.base)
            return None
        dt = attr.data_type.base
        try:
            # Already typed by DB driver, but ensure correct ScalarType
            if dt == ScalarType.INT:
                if isinstance(raw, bool):  # bool is subclass of int
                    return DataValue(scalar_type=ScalarType.BOOLEAN, value=raw, lexical_value=str(raw))
                return DataValue(scalar_type=ScalarType.INT, value=int(raw), lexical_value=str(raw))
            elif dt == ScalarType.LONG:
                return DataValue(scalar_type=ScalarType.LONG, value=int(raw), lexical_value=str(raw))
            elif dt == ScalarType.FLOAT:
                return DataValue(scalar_type=ScalarType.FLOAT, value=float(raw), lexical_value=str(raw))
            elif dt == ScalarType.DOUBLE:
                return DataValue(scalar_type=ScalarType.DOUBLE, value=float(raw), lexical_value=str(raw))
            elif dt == ScalarType.DECIMAL:
                if isinstance(raw, Decimal):
                    return DataValue(scalar_type=ScalarType.DECIMAL, value=raw, lexical_value=str(raw))
                return DataValue(scalar_type=ScalarType.DECIMAL, value=Decimal(str(raw)), lexical_value=str(raw))
            elif dt == ScalarType.BOOLEAN:
                return DataValue(scalar_type=ScalarType.BOOLEAN, value=bool(raw), lexical_value=str(raw))
            elif dt == ScalarType.DATETIME:
                if isinstance(raw, datetime):
                    return DataValue(scalar_type=ScalarType.DATETIME, value=raw.isoformat(), lexical_value=raw.isoformat())
                return DataValue(scalar_type=ScalarType.DATETIME, value=str(raw), lexical_value=str(raw))
            elif dt == ScalarType.DATE:
                if isinstance(raw, date):
                    return DataValue(scalar_type=ScalarType.DATE, value=raw.isoformat(), lexical_value=raw.isoformat())
                return DataValue(scalar_type=ScalarType.DATE, value=str(raw), lexical_value=str(raw))
            elif dt == ScalarType.TIME:
                if isinstance(raw, time):
                    return DataValue(scalar_type=ScalarType.TIME, value=raw.isoformat(), lexical_value=raw.isoformat())
                return DataValue(scalar_type=ScalarType.TIME, value=str(raw), lexical_value=str(raw))
            elif dt == ScalarType.UUID:
                if isinstance(raw, uuid.UUID):
                    return DataValue(scalar_type=ScalarType.UUID, value=str(raw), lexical_value=str(raw))
                return DataValue(scalar_type=ScalarType.UUID, value=str(raw), lexical_value=str(raw))
            elif dt == ScalarType.BINARY:
                if isinstance(raw, bytes):
                    b64 = base64.b64encode(raw).decode()
                    return DataValue(scalar_type=ScalarType.BINARY, value=raw, lexical_value=b64)
                # assume base64 string
                return DataValue(scalar_type=ScalarType.BINARY, value=base64.b64decode(raw), lexical_value=raw)
            elif dt == ScalarType.JSON:
                if isinstance(raw, str):
                    return DataValue(scalar_type=ScalarType.JSON, value=json.loads(raw), lexical_value=raw)
                return DataValue(scalar_type=ScalarType.JSON, value=raw, lexical_value=json.dumps(raw))
            else:
                return scalar_value(raw)
        except Exception:
            return scalar_value(raw)

    def _parse_default(self, default_str: str, base_type: ScalarType) -> DataValue:
        try:
            if base_type == ScalarType.INT:
                return DataValue(scalar_type=ScalarType.INT, value=int(default_str), lexical_value=default_str)
            if base_type == ScalarType.FLOAT or base_type == ScalarType.DOUBLE:
                return DataValue(scalar_type=ScalarType.FLOAT, value=float(default_str), lexical_value=default_str)
            if base_type == ScalarType.BOOLEAN:
                val = default_str.lower() in ('true', '1', 'yes')
                return DataValue(scalar_type=ScalarType.BOOLEAN, value=val, lexical_value=default_str)
        except Exception:
            pass
        return scalar_value(default_str)




