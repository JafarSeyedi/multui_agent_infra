# engines/document/writers/dsdm_writers/bson_writer.py
"""BSON writer using standalone bson library."""
from __future__ import annotations

import bson
from ...models.dsdm_models import DataNode
from ...parsers.dsdm_parsers.dsdm_utils import node_to_python
from .base_dsdm_writer import BaseDSDMWriter, DSDMWriteOptions


class BSONWriter(BaseDSDMWriter):
    name = "bson"
    supported_extensions = (".bson",)
    media_type_str = "application/bson"

    def get_supported_media_types(self) -> list[str]:
        return [self.media_type_str]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    async def _serialise_root(self, root_node: DataNode, options: DSDMWriteOptions) -> bytes:
        py_obj = node_to_python(root_node)
        # The standalone bson library expects a list of dicts for dumps; single dict is also ok?
        # bson.dumps expects a dict, not a list. If root is a list, wrap or raise.
        if isinstance(py_obj, list):
            # We'll serialize the list as a top-level document with key "documents"
            wrapper_key = options.custom.get("bson_wrapper_key", "documents") if options.custom else "documents"
            py_obj = {wrapper_key: py_obj}
        return bson.encode(py_obj)

    async def _serialise_node(self, node: DataNode, options: DSDMWriteOptions) -> bytes:
        return await self._serialise_root(node, options)