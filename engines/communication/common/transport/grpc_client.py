"""gRPC transport implementation for operation-style calls.

The adapter intentionally uses low-level dynamic stubs, which avoids a hard dependency on
statically generated service classes and keeps integration generic across service definitions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from collections.abc import Callable
from urllib.parse import urlsplit

from .base import AbstractTransport, TransportRequest, TransportResponse


def _extract_target_and_method(url: str, params: dict[str, Any]) -> tuple[str, str | None]:
    """Return target host and optional gRPC method path from a URL-like value."""
    target = url
    method = params.get("grpc_method") or params.get("_grpc_method") or params.get("method")

    if method:
        return target, str(method)

    parsed = urlsplit(url)
    if parsed.scheme and parsed.netloc:
        target = parsed.netloc
        if parsed.path:
            method = parsed.path.lstrip("/")
    elif url.startswith("grpc://"):
        target = url[len("grpc://") :]
        if "/" in target:
            target, method = target.split("/", 1)
    elif "/" in url and not url.startswith("/"):
        target, method = url.split("/", 1)

    if method:
        method = method.lstrip("/")

    return target, method


class GRPCTransport(AbstractTransport):
    """Generic grpc transport with dynamic unary/streaming invocations."""

    name = "gRPC"

    def __init__(
        self,
        *,
        use_tls: bool = False,
        tls_cert: str | None = None,
        tls_key: str | None = None,
        tls_ca: str | None = None,
        tls_ca_file: str | None = None,
        max_retries: int = 0,
    ) -> None:
        self.use_tls = use_tls
        self.tls_cert = tls_cert
        self.tls_key = tls_key
        self.tls_ca = tls_ca
        self.tls_ca_file = tls_ca_file
        self.max_retries = max_retries
        self._grpc: Any | None = None
        self._channels: dict[str, Any] = {}

    def _load_grpc(self) -> Any:
        if self._grpc is not None:
            return self._grpc

        try:
            import grpc  # type: ignore[import-not-found]
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("grpcio is required for GRPCTransport") from exc
        self._grpc = grpc
        return grpc

    def _make_ssl_credentials(self):
        grpc = self._load_grpc()
        if not self.use_tls:
            return None

        cert = self.tls_cert
        key = self.tls_key
        ca = self.tls_ca
        ca_file = self.tls_ca_file

        if cert and key:
            cert_chain = cert
            private_key = key
        else:
            cert_chain = None
            private_key = None

        if ca_file or ca:
            return grpc.ssl_channel_credentials(
                root_certificates=(Path(ca_file).read_bytes() if ca_file else ca.encode("utf-8")),
                private_key=(Path(key).read_bytes() if (key and not isinstance(key, str)) else cert_chain.encode("utf-8") if isinstance(cert_chain, str) and cert_chain else None),
                certificate_chain=(cert_chain.encode("utf-8") if isinstance(cert_chain, str) else None),
            )

        if not key and not cert:
            return grpc.ssl_channel_credentials()

        return grpc.ssl_channel_credentials(
            private_key=private_key.encode("utf-8") if isinstance(private_key, str) else private_key,
            certificate_chain=cert_chain.encode("utf-8") if isinstance(cert_chain, str) else cert_chain,
        )

    def _get_channel(self, target: str):
        if target in self._channels:
            return self._channels[target]

        grpc = self._load_grpc()
        if self.use_tls:
            creds = self._make_ssl_credentials()
            channel = grpc.aio.secure_channel(target, creds)
        else:
            channel = grpc.aio.insecure_channel(target)

        self._channels[target] = channel
        return channel

    async def send(
        self,
        request: TransportRequest,
        *,
        payload_serializer: Callable[[Any], bytes] | None = None,
        content_type: str | None = None,
    ) -> TransportResponse:
        body = request.body
        if payload_serializer is not None and body is not None:
            body = payload_serializer(body)
        elif isinstance(body, str):
            body = body.encode("utf-8")
        elif body is None:
            body = b""

        target, method = _extract_target_and_method(request.url, request.params)
        if not method:
            raise ValueError("gRPC transport requires method path; set request params 'grpc_method' or include path")

        request.params = dict(request.params)
        stream_output = bool(request.params.pop("grpc_stream", False) or request.params.pop("grpc_stream_response", False))
        stream_input = bool(request.params.pop("grpc_stream_request", False))

        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                return await self._send_once(target, method, body, stream_output, stream_input)
            except Exception as err:  # pragma: no cover - delegated network failures
                last_error = err
                if attempt >= self.max_retries:
                    raise
                await _backoff_sleep(attempt)

        if last_error is not None:
            raise last_error
        raise RuntimeError("grpc call failed")

    async def _send_once(
        self,
        target: str,
        method: str,
        body: bytes | bytearray,
        stream_output: bool,
        stream_input: bool,
    ) -> TransportResponse:
        channel = self._get_channel(target)

        if stream_output and not stream_input:
            call = channel.unary_stream(
                f"/{method}",
                request_serializer=_identity_serialized_bytes,
                response_deserializer=_identity_serialized_bytes,
            )
            items: list[bytes] = []
            async for item in call(body):
                if isinstance(item, bytes):
                    items.append(item)
                elif isinstance(item, bytearray):
                    items.append(bytes(item))
                else:
                    items.append(str(item).encode("utf-8"))
            return TransportResponse(
                status_code=0,
                headers={},
                body=b"\n".join(items),
                elapsed_ms=0,
                transport="gRPC",
                metadata={"target": target, "method": method, "stream": True},
            )

        call = channel.unary_unary(
            f"/{method}",
            request_serializer=_identity_serialized_bytes,
            response_deserializer=_identity_serialized_bytes,
        )
        response = await call(body)

        if isinstance(response, (bytes, bytearray)):
            payload = bytes(response)
        else:
            payload = str(response).encode("utf-8")

        return TransportResponse(
            status_code=0,
            headers={},
            body=payload,
            elapsed_ms=0,
            transport="gRPC",
            metadata={"target": target, "method": method},
        )

    async def close(self) -> None:
        if not self._channels:
            return
        for channel in self._channels.values():
            await channel.close(grace=None)
        self._channels = {}


def _identity_serialized_bytes(value: bytes | bytearray | str | None) -> bytes:
    if value is None:
        return b""
    if isinstance(value, (bytes, bytearray)):
        return bytes(value)
    if isinstance(value, str):
        return value.encode("utf-8")
    return bytes(str(value), "utf-8")


async def _backoff_sleep(attempt: int) -> None:
    import asyncio

    delay = min(2.0, 0.1 * 2**attempt)
    await asyncio.sleep(delay)
