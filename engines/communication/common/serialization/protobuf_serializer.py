"""Minimal protobuf serializer helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .avro_serializer import MessageSerializer


@dataclass
class ProtobufMessageSpec:
    module: str
    class_name: str


def _load_message_class(spec: ProtobufMessageSpec):
    module_path, _, _ = spec.module.rpartition(".")
    module = __import__(module_path, fromlist=[spec.class_name])
    return getattr(module, spec.class_name)


class ProtobufSerializer(MessageSerializer):
    content_type = "application/x-protobuf"

    def __init__(self, message_spec: ProtobufMessageSpec | None = None) -> None:
        self.message_spec = message_spec

    def serialize(self, payload: Any) -> bytes:
        if self.message_spec is None:
            raise ValueError("ProtobufSerializer requires message_spec")
        cls = _load_message_class(self.message_spec)
        if hasattr(cls, "SerializeToString"):
            return payload.SerializeToString() if isinstance(payload, cls) else cls(**payload).SerializeToString()
        if isinstance(payload, (bytes, bytearray)):
            return bytes(payload)
        raise TypeError("Payload must be protobuf message or mapping")

    def deserialize(self, data: bytes | str) -> Any:
        if self.message_spec is None:
            raise ValueError("ProtobufSerializer requires message_spec")
        cls = _load_message_class(self.message_spec)
        msg = cls()
        if hasattr(msg, "ParseFromString"):
            if isinstance(data, str):
                data = data.encode("utf-8")
            msg.ParseFromString(data)
            return msg
        raise TypeError("Invalid protobuf message class")
