"""Base transport primitives for communication adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TransportRequest:
    url: str
    method: str
    headers: dict[str, str] = field(default_factory=dict)
    params: dict[str, Any] = field(default_factory=dict)
    cookies: dict[str, str] = field(default_factory=dict)
    timeout_ms: int = 30000
    body: bytes | str | None = None


@dataclass
class TransportResponse:
    status_code: int
    headers: dict[str, Any]
    body: bytes
    elapsed_ms: float
    transport: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def json(self) -> Any:
        text = self.body.decode("utf-8") if isinstance(self.body, (bytes, bytearray)) else str(self.body)
        if not text:
            return None
        try:
            import json
            return json.loads(text)
        except Exception:
            return text


class AbstractTransport(ABC):
    name = "base"

    @abstractmethod
    async def send(self, request: TransportRequest, *, payload_serializer=None, content_type: str | None = None) -> TransportResponse:
        """Send an operation-specific payload and return a generic response."""
        raise NotImplementedError

    async def close(self) -> None:
        """Release underlying resources."""
        return None
