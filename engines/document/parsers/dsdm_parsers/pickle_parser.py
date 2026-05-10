# engines/document/parsers/dsdm_parsers/pickle_parser.py
"""Pickle parser."""
import pickle
from .binary_parser import BinaryParser
from .dsdm_utils import build_node_from_python
from ...models.dsdm_models import DataNode


class PickleParser(BinaryParser):
    name = "pickle"
    supported_extensions = (".pickle", ".pkl")

    async def _parse_to_datanode(self, raw_bytes: bytes, options=None) -> DataNode:
        if options and not options.unsafe_operations_allowed:
            raise ValueError("Pickle parsing requires 'unsafe_operations_allowed' flag")
        data = pickle.loads(raw_bytes)
        return build_node_from_python(data, path="$")

    def _detect_media_type(self, source_name: str) -> str:
        return "application/python-pickle"