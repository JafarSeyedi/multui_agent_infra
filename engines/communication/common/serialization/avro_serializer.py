"""Optional Avro serializer with graceful fallback when fastavro is unavailable."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class MessageSerializer(ABC):
    content_type = "application/octet-stream"

    @abstractmethod
    def serialize(self, payload: Any) -> bytes:
        ...

    @abstractmethod
    def deserialize(self, data: bytes | str) -> Any:
        ...


class AvroSerializer(MessageSerializer):
    content_type = "application/avro+binary"

    def __init__(self, *, schema: dict[str, Any] | None = None) -> None:
        self.schema = schema

    def serialize(self, payload: Any) -> bytes:
        if self.schema is None:
            # Fallback: use JSON-like utf-8 bytes to keep transport functioning.
            import json

            return json.dumps(payload).encode("utf-8")

        try:
            from fastavro import schemaless_writer  # type: ignore[import-not-found]
            import io
        except Exception:
            import json
            return json.dumps(payload).encode("utf-8")

        buffer = io.BytesIO()
        schemaless_writer(buffer, self.schema, payload)
        return buffer.getvalue()

    def deserialize(self, data: bytes | str) -> Any:
        if self.schema is None:
            import json
            if isinstance(data, str):
                data = data.encode("utf-8")
            return json.loads(data.decode("utf-8"))

        try:
            from fastavro import schemaless_reader  # type: ignore[import-not-found]
            import io
        except Exception:
            import json
            if isinstance(data, str):
                return json.loads(data)
            return json.loads(data.decode("utf-8"))

        if isinstance(data, str):
            data = data.encode("utf-8")
        buffer = io.BytesIO(data)
        return schemaless_reader(buffer, self.schema)
