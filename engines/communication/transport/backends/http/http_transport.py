# engines/communication/transport/backends/http/http_transport.py
from __future__ import annotations

from ...plugin import BaseTransport


class HttpTransport(BaseTransport):
    """HTTP/HTTPS transport using aiohttp."""

    name = "http"

    def __init__(self) -> None:
        self._session = None

    async def connect(self, endpoint: str) -> None:
        try:
            import aiohttp
        except ImportError as exc:
            raise RuntimeError("aiohttp is required for HTTP transport") from exc
        self._session = aiohttp.ClientSession()

    async def send_bytes(self, data: bytes, endpoint: str) -> bytes:
        if self._session is None:
            raise RuntimeError("Transport not connected")
        async with self._session.post(endpoint, data=data) as resp:
            return await resp.read()

    async def close(self) -> None:
        if self._session:
            await self._session.close()
            self._session = None
