# engines/document/parsers/dsdm_parsers/binary_parser.py
"""Generic binary parser (passthrough)."""
from .base_dsdm_parser import BaseDSDMParser, DSDMParseOptions
from .dsdm_utils import scalar_value
from ...models.dsdm_models import DataNode, DataNodeKind


class BinaryParser(BaseDSDMParser):
    name = "binary"
    supported_extensions: tuple[str, ...] = ()   # type annotation allows subclasses to override

    async def _parse_to_datanode(self, raw_bytes: bytes, options: DSDMParseOptions) -> DataNode:
        return DataNode(
            node_id="node:$",
            kind=DataNodeKind.SCALAR,
            path="$",
            name="binary_data",
            value=scalar_value(raw_bytes)
        )

    def _detect_media_type(self, source_name: str) -> str:
        return "application/octet-stream"