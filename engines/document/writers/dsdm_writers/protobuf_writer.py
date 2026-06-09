# engines/document/writers/dsdm_writers/protobuf_writer.py
"""Protobuf writer using a FileDescriptorSet."""
from __future__ import annotations

from google.protobuf import descriptor_pool, message_factory
from google.protobuf.descriptor_pb2 import FileDescriptorSet
from google.protobuf.json_format import ParseDict

from ...models.dsdm_models import DataNode
from ...parsers.dsdm_parsers.dsdm_utils import node_to_python
from .base_dsdm_writer import BaseDSDMWriter, DSDMWriteOptions


class ProtobufWriter(BaseDSDMWriter):
    name = "protobuf"
    supported_extensions = (".pb",)
    media_type_str = "application/protobuf"

    def get_supported_media_types(self) -> list[str]:
        return [self.media_type_str]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    async def _serialise_root(self, root_node: DataNode, options: DSDMWriteOptions) -> bytes:
        fds_bytes = options.custom.get("protobuf_descriptor")
        message_name = options.custom.get("message_name")
        if not fds_bytes or not message_name:
            raise ValueError("Protobuf writing requires 'protobuf_descriptor' and 'message_name' in options.custom")

        pool = descriptor_pool.DescriptorPool()
        fds = FileDescriptorSet.FromString(fds_bytes)
        for fd in fds.file:
            pool.Add(fd)
        descriptor = pool.FindMessageTypeByName(message_name)
        factory = message_factory.MessageFactory(pool=pool)
        msg_class = factory.GetPrototype(descriptor)  # type: ignore[attr-defined]
        msg = msg_class()

        py_obj = node_to_python(root_node)
        ParseDict(py_obj, msg)
        return msg.SerializeToString()

    async def _serialise_node(self, node: DataNode, options: DSDMWriteOptions) -> bytes:
        return await self._serialise_root(node, options)