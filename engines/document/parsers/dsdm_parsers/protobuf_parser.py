# engines/document/parsers/dsdm_parsers/protobuf_parser.py
"""Protobuf parser."""
from google.protobuf import descriptor_pool, message_factory
from google.protobuf.descriptor_pb2 import FileDescriptorSet
from google.protobuf.json_format import MessageToDict
from .base_dsdm_parser import BaseDSDMParser, DSDMParseOptions
from .dsdm_utils import build_node_from_python
from ...models.dsdm_models import DataNode


class ProtobufParser(BaseDSDMParser):
    name = "protobuf"
    supported_extensions = (".pb",)

    async def _parse_to_datanode(self, raw_bytes: bytes, options: DSDMParseOptions) -> DataNode:
        fds_bytes = options.custom.get("protobuf_descriptor")
        message_name = options.custom.get("message_name")
        if not fds_bytes or not message_name:
            raise ValueError("Protobuf parsing requires 'protobuf_descriptor' and 'message_name' in options.custom")

        pool = descriptor_pool.DescriptorPool()
        fds = FileDescriptorSet.FromString(fds_bytes)
        for fd in fds.file:
            pool.Add(fd)
        descriptor = pool.FindMessageTypeByName(message_name)
        factory = message_factory.MessageFactory(pool=pool)
        msg_class = factory.GetPrototype(descriptor)  # type: ignore[attr-defined]
        msg = msg_class()
        msg.ParseFromString(raw_bytes)

        data_dict = MessageToDict(msg, preserving_proto_field_name=True)  # type: ignore[call-arg]  # including_default_value_fields removed
        return build_node_from_python(data_dict, path="$")

    def _detect_media_type(self, source_name: str) -> str:
        return "application/protobuf"