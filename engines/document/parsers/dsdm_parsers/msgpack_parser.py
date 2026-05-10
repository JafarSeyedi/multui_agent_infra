# engines/document/parsers/dsdm_parsers/msgpack_parser.py
"""MessagePack parser."""
import msgpack  # type: ignore[import-untyped]
from .binary_parser import BinaryParser
from .dsdm_utils import build_node_from_python
from ...models.dsdm_models import DataNode


class MsgPackParser(BinaryParser):
    name = "msgpack"
    supported_extensions = (".msgpack",)

    async def _parse_to_datanode(self, raw_bytes: bytes, options=None) -> DataNode:
        data = msgpack.unpackb(raw_bytes, raw=False)
        return build_node_from_python(data, path="$")

    def _detect_media_type(self, source_name: str) -> str:
        return "application/msgpack"