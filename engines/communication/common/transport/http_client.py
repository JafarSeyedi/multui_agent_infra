"""HTTP/HTTP2 transport implementation used by service consumers and exposed bridges."""

from __future__ import annotations

import asyncio
import ssl
from time import perf_counter
from typing import Any, Callable

from .base import AbstractTransport, TransportRequest, TransportResponse


class HTTPTransport(AbstractTransport):
    """Asynchronous HTTP transport backed by :mod:`aiohttp`.

    The transport is intentionally defensive: all third‑party imports are performed
    lazily so the module import itself remains optional in environments without
    network dependencies.
    """

    name = "HTTP"

    def __init__(
        self,
        *,
        timeout_ms: int = 30000,
        tls_context: ssl.SSLContext | None = None,
        max_retries: int = 0,
        max_connections: int = 100,
        default_headers: dict[str, str] | None = None,
    ) -> None:
        self._timeout_ms = timeout_ms
        self._tls_context = tls_context
        self._max_retries = max_retries
        self._max_connections = max_connections
        self._default_headers = default_headers or {}
        self._session: Any | None = None
        self._session_closed = False

    async def close(self) -> None:
        if self._session is not None:
            await self._session.close()
            self._session = None

    async def send(
        self,
        request: TransportRequest,
        *,
        payload_serializer: Callable[[Any], bytes] | None = None,
        content_type: str | None = None,
    ) -> TransportResponse:
        body = request.body
        if body is not None and payload_serializer is not None and not isinstance(body, (bytes, bytearray, str)):
            body = payload_serializer(body)
        elif body is not None and isinstance(body, (dict, list)):
            body = str(body).encode("utf-8")

        headers = dict(self._default_headers)
        headers.update(request.headers)

        if content_type and "Content-Type" not in {k.lower() for k in headers}:
            headers["Content-Type"] = content_type

        params = dict(request.params)

        last_error: Exception | None = None
        for attempt in range(max(0, self._max_retries) + 1):
            try:
                return await self._send_once(request, headers, params, body)
            except Exception as err:  # pragma: no cover - transport failures are delegated
                last_error = err
                if attempt >= self._max_retries:
                    raise
                await asyncio.sleep(min(1.0, 0.05 * (2**attempt)))

        if last_error is not None:
            raise last_error

        raise RuntimeError("HTTP transport failed without concrete exception")

    async def _send_once(
        self,
        request: TransportRequest,
        headers: dict[str, str],
        params: dict[str, Any],
        body: bytes | str | None,
    ) -> TransportResponse:
        timeout_ms = request.timeout_ms or self._timeout_ms

        try:
            import aiohttp  # type: ignore[import-not-found]
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("aiohttp is required for HTTPTransport") from exc

        timeout = aiohttp.ClientTimeout(total=timeout_ms / 1000)
        session = await self._ensure_session(timeout)

        start = perf_counter()
        async with session.request(
            method=request.method,
            url=request.url,
            headers=headers,
            params=params,
            cookies=request.cookies or None,
            data=None if body is None else body,
            timeout=timeout,
        ) as response:
            elapsed_ms = (perf_counter() - start) * 1000
            response_body = await response.read()
            return TransportResponse(
                status_code=response.status,
                headers=dict(response.headers),
                body=response_body,
                elapsed_ms=elapsed_ms,
                transport="HTTP",
                metadata={"url": str(response.url), "reason": response.reason},
            )

    async def _ensure_session(self, timeout: Any):
        if self._session is None:
            try:
                import aiohttp  # type: ignore[import-not-found]
                import asyncio as _asyncio
            except Exception as exc:  # pragma: no cover
                raise RuntimeError("aiohttp is required for HTTPTransport") from exc

            connector = aiohttp.TCPConnector(
                ssl=self._tls_context if self._tls_context is not None else False,
                limit=self._max_connections,
                enable_cleanup_closed=True,
                ttl_dns_cache=300,
            )
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                auto_decompress=False,
                raise_for_status=False,
            )
            _asyncio.get_running_loop().call_soon(self._register_shutdown)
        return self._session

    def _register_shutdown(self) -> None:  # pragma: no cover
        if self._session_closed:
            return
        self._session_closed = True
        try:
            loop = asyncio.get_running_loop()
            loop.call_later(0, lambda: None)
        except RuntimeError:
            # No running loop in current context is fine.
            return
