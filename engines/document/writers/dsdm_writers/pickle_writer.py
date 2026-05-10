# engines/document/writers/dsdm_writers/pickle_writer.py
"""Pickle writer with safety flag."""
from __future__ import annotations

import pickle

from ...parsers.dsdm_parsers.dsdm_utils import node_to_python
from ...models.dsdm_models import DataNode
from .base_dsdm_writer import BaseDSDMWriter, DSDMWriteOptions


class PickleWriter(BaseDSDMWriter):
    name = "pickle"
    supported_extensions = (".pickle", ".pkl")
    media_type_str = "application/python-pickle"

    def get_supported_media_types(self) -> list[str]:
        return [self.media_type_str]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    async def _serialise_root(self, root_node: DataNode, options: DSDMWriteOptions) -> bytes:
        if not options.unsafe_operations_allowed:
            raise ValueError("Pickle writing requires 'unsafe_operations_allowed' flag")
        py_obj = node_to_python(root_node)
        return pickle.dumps(py_obj)

    async def _serialise_node(self, node: DataNode, options: DSDMWriteOptions) -> bytes:
        return await self._serialise_root(node, options)