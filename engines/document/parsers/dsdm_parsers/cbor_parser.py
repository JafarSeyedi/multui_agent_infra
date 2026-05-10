# engines/document/parsers/dsdm_parsers/cbor_parser.py
"""CBOR parser."""
import cbor2
from .binary_parser import BinaryParser
from .dsdm_utils import build_node_from_python
from ...models.dsdm_models import DataNode


class CBORParser(BinaryParser):
    name = "cbor"
    supported_extensions = (".cbor",)

    async def _parse_to_datanode(self, raw_bytes: bytes, options=None) -> DataNode:
        data = cbor2.loads(raw_bytes)
        return build_node_from_python(data, path="$")

    def _detect_media_type(self, source_name: str) -> str:
        return "application/cbor"