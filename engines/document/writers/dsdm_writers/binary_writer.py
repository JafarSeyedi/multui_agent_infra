# engines/document/writers/dsdm_writers/binary_writer.py
"""Configurable binary writer (raw passthrough or structured)."""
from __future__ import annotations

import msgpack  # type: ignore[import-untyped]
import cbor2
import bson
import pickle
from typing import Any, Callable

from ...models.dsdm_models import DataNode, DataNodeKind
from ...parsers.dsdm_parsers.dsdm_utils import node_to_python
from .base_dsdm_writer import BaseDSDMWriter, DSDMWriteOptions


class BinaryWriter(BaseDSDMWriter):
    name = "binary"
    supported_extensions = (".bin",)
    media_type_str = "application/octet-stream"

    def get_supported_media_types(self) -> list[str]:
        return [self.media_type_str]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    async def _serialise_root(self, root_node: DataNode, options: DSDMWriteOptions) -> bytes:
        # Raw passthrough
        if root_node.kind == DataNodeKind.SCALAR and root_node.value and root_node.value.scalar_type == "binary":
            return root_node.value.value if isinstance(root_node.value.value, bytes) else bytes(root_node.value.value)

        fmt = options.custom.get("binary_format", "msgpack").lower() if options.custom else "msgpack"
        py_obj = node_to_python(root_node)

        if fmt == "msgpack":
            return msgpack.packb(py_obj, use_bin_type=True)
        elif fmt == "cbor":
            return cbor2.dumps(py_obj)
        elif fmt == "bson":
            if isinstance(py_obj, list):
                py_obj = {"documents": py_obj}
            return bson.dumps(py_obj)  # type: ignore[attr-defined]
        elif fmt == "pickle":
            if not options.unsafe_operations_allowed:
                raise ValueError("Pickle writing requires 'unsafe_operations_allowed' flag")
            return pickle.dumps(py_obj)
        else:
            return msgpack.packb(py_obj, use_bin_type=True)

    async def _serialise_node(self, node: DataNode, options: DSDMWriteOptions) -> bytes:
        return await self._serialise_root(node, options)