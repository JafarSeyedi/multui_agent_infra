# engines/document/parsers/dsdm_parsers/bson_parser.py
"""BSON parser using standalone bson library."""
from __future__ import annotations

import bson
from .binary_parser import BinaryParser
from .dsdm_utils import build_node_from_python, scalar_value
from ...models.dsdm_models import DataNode


class BSONParser(BinaryParser):
    name = "bson"
    supported_extensions = (".bson",)

    async def _parse_to_datanode(self, raw_bytes: bytes, options=None) -> DataNode:
        data = bson.loads(raw_bytes)   # returns list of dicts
        if isinstance(data, list):
            if len(data) == 1:
                return build_node_from_python(data[0], path="$")
            return build_node_from_python(data, path="$")
        return build_node_from_python(data, path="$")

    def _detect_media_type(self, source_name: str) -> str:
        return "application/bson"