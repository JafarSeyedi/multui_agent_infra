"""JSON serializer used by all network transports."""

from __future__ import annotations

import json
from typing import Any

from .avro_serializer import MessageSerializer


class JSONSerializer(MessageSerializer):
    content_type = "application/json"

    def serialize(self, payload: Any) -> bytes:
        if isinstance(payload, (bytes, bytearray)):
            return bytes(payload)
        return json.dumps(payload, ensure_ascii=False).encode("utf-8")

    def deserialize(self, data: bytes | str | bytearray) -> Any:
        if data is None:
            return None
        if isinstance(data, bytearray):
            data = bytes(data)
        if isinstance(data, (bytes, bytearray)):
            data = data.decode("utf-8")
        text = str(data).strip()
        if not text:
            return None
        return json.loads(text)
