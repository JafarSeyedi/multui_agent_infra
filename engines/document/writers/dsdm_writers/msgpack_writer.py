# engines/document/writers/dsdm_writers/msgpack_writer.py
"""MessagePack writer."""
from __future__ import annotations

import msgpack  # type: ignore[import-untyped]

from ...parsers.dsdm_parsers.dsdm_utils import node_to_python
from ...models.dsdm_models import DataNode
from .base_dsdm_writer import BaseDSDMWriter, DSDMWriteOptions


class MsgPackWriter(BaseDSDMWriter):
    name = "msgpack"
    supported_extensions = (".msgpack",)
    media_type_str = "application/msgpack"

    def get_supported_media_types(self) -> list[str]:
        return [self.media_type_str]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    async def _serialise_root(self, root_node: DataNode, options: DSDMWriteOptions) -> bytes:
        py_obj = node_to_python(root_node)
        return msgpack.packb(py_obj, use_bin_type=True)

    async def _serialise_node(self, node: DataNode, options: DSDMWriteOptions) -> bytes:
        return await self._serialise_root(node, options)