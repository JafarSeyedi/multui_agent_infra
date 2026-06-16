# engines/communication/transport/plugin.py
from __future__ import annotations

from abc import ABC, abstractmethod


class BaseTransport(ABC):
    """Low-level wire protocol transport.

    Transports handle the raw byte/stream layer. Channel backends
    use transports for actual wire communication.
    """

    name: str = "base"

    @abstractmethod
    async def send_bytes(self, data: bytes, endpoint: str) -> bytes:
        ...

    @abstractmethod
    async def connect(self, endpoint: str) -> None:
        ...

    @abstractmethod
    async def close(self) -> None:
        ...
