# engines/document/parsers/dsdm_parsers/csv_tsv_parser.py
"""CSV/TSV parser with schema-driven type coercion."""
from __future__ import annotations

import csv
import io
from datetime import datetime, date, time
from typing import Any

from .base_dsdm_parser import BaseDSDMParser, DSDMParseOptions
from .dsdm_utils import scalar_value
from ...models.dsdm_models import DataNode, DataNodeKind, DataValue
from ...models.msdm_models import Entity, Attribute, ScalarType


class CSVTSVParser(BaseDSDMParser):
    name = "csv_tsv"
    supported_extensions = (".csv", ".tsv", ".tab")

    async def _parse_to_datanode(self, raw_bytes: bytes, options: DSDMParseOptions) -> DataNode:
        encoding = options.encoding
        # Use explicit keyword arguments for csv.reader
        delimiter = options.custom.get("delimiter", ",") if options.custom else ","
        quotechar = options.custom.get("quotechar", '"') if options.custom else '"'
        escapechar = options.custom.get("escapechar", None) if options.custom else None
        doublequote = options.custom.get("doublequote", True) if options.custom else True
        skipinitialspace = options.custom.get("skipinitialspace", False) if options.custom else False
        lineterminator = options.custom.get("lineterminator", "\r\n") if options.custom else "\r\n"

        text = raw_bytes.decode(encoding)
        reader = csv.reader(
            io.StringIO(text),
            delimiter=delimiter,
            quotechar=quotechar,
            escapechar=escapechar,
            doublequote=doublequote,
            skipinitialspace=skipinitialspace,
            lineterminator=lineterminator,
        )
        rows = list(reader)
        if not rows:
            return DataNode(node_id="node:$", kind=DataNodeKind.ARRAY, path="$", name="root")

        entity: Entity | None = None
        if options.msdm_schema and options.msdm_schema.entities:
            entity = options.msdm_schema.entities[0]

        if entity and entity.attributes:
            header_row = rows[0]
            data_rows = rows[1:]
            attr_map: dict[int, Attribute] = {}
            attr_by_name = {attr.name.lower().strip(): attr for attr in entity.attributes}
            for idx, col_name in enumerate(header_row):
                attr = attr_by_name.get(col_name.lower().strip())
                if attr:
                    attr_map[idx] = attr
        else:
            header_row = rows[0]
            data_rows = rows[1:]
            attr_map = {}

        array_node = DataNode(node_id="node:$", kind=DataNodeKind.ARRAY, path="$", name="rows")
        for row_idx, row in enumerate(data_rows):
            obj_node = DataNode(node_id=f"node:$[{row_idx}]", kind=DataNodeKind.OBJECT,
                                path=f"$[{row_idx}]", name=str(row_idx))
            if attr_map and entity:
                for attr in entity.attributes:
                    col_idx = next((idx for idx, a in attr_map.items() if a is attr), None)
                    raw_val = row[col_idx] if col_idx is not None and col_idx < len(row) else None
                    value = self._coerce_value(raw_val, attr)
                    if value is None and attr.required:
                        obj_node.metadata["_required_missing"] = True
                    obj_node.children.append(DataNode(
                        node_id=f"node:$[{row_idx}].{attr.name}",
                        kind=DataNodeKind.SCALAR,
                        path=f"$[{row_idx}].{attr.name}",
                        name=attr.name,
                        value=value,
                    ))
            else:
                for col_idx, raw_val in enumerate(row):
                    key = header_row[col_idx] if col_idx < len(header_row) else f"col{col_idx}"
                    obj_node.children.append(DataNode(
                        node_id=f"node:$[{row_idx}].{key}",
                        kind=DataNodeKind.SCALAR,
                        path=f"$[{row_idx}].{key}",
                        name=key,
                        value=scalar_value(raw_val)
                    ))
            array_node.children.append(obj_node)
        return array_node

    def _coerce_value(self, raw: str | None, attr: Attribute) -> DataValue | None:
        if raw is None or raw.strip() == '':
            if attr.default_value is not None:
                return self._coerce_default_value(attr)
            return None
        dt = attr.data_type.base
        try:
            if dt == ScalarType.INT:
                return DataValue(scalar_type=ScalarType.INT, value=int(raw), lexical_value=raw)
            elif dt == ScalarType.LONG:
                return DataValue(scalar_type=ScalarType.LONG, value=int(raw), lexical_value=raw)
            elif dt == ScalarType.FLOAT:
                return DataValue(scalar_type=ScalarType.FLOAT, value=float(raw), lexical_value=raw)
            elif dt == ScalarType.DOUBLE:
                return DataValue(scalar_type=ScalarType.DOUBLE, value=float(raw), lexical_value=raw)
            elif dt == ScalarType.DECIMAL:
                from decimal import Decimal
                return DataValue(scalar_type=ScalarType.DECIMAL, value=Decimal(raw), lexical_value=raw)
            elif dt == ScalarType.BOOLEAN:
                val = raw.lower() in ('true', '1', 'yes')
                return DataValue(scalar_type=ScalarType.BOOLEAN, value=val, lexical_value=raw)
            elif dt == ScalarType.DATETIME:
                return DataValue(scalar_type=ScalarType.DATETIME, value=datetime.fromisoformat(raw).isoformat(), lexical_value=raw)
            elif dt == ScalarType.DATE:
                return DataValue(scalar_type=ScalarType.DATE, value=date.fromisoformat(raw).isoformat(), lexical_value=raw)
            elif dt == ScalarType.TIME:
                return DataValue(scalar_type=ScalarType.TIME, value=time.fromisoformat(raw).isoformat(), lexical_value=raw)
            elif dt == ScalarType.UUID:
                import uuid
                return DataValue(scalar_type=ScalarType.UUID, value=str(uuid.UUID(raw)), lexical_value=raw)
            elif dt == ScalarType.BINARY:
                import base64
                return DataValue(scalar_type=ScalarType.BINARY, value=base64.b64decode(raw), lexical_value=raw)
            else:
                return scalar_value(raw)
        except Exception:
            return scalar_value(raw)

    def _detect_media_type(self, source_name: str) -> str:
        return "text/csv"