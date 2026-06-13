"""Factory pattern — creates and caches transport instances."""

from __future__ import annotations

from typing import Any

from ...document.models.ssdm_models import Transport
from ..common.transport.base import AbstractTransport
from ..common.transport.amqp_client import AMQPTransport
from ..common.transport.grpc_client import GRPCTransport
from ..common.transport.http_client import HTTPTransport
from ..common.transport.kafka_client import KafkaTransport


class TransportFactory:
    """Creates and caches transport instances by Transport enum."""

    def __init__(self, overrides: dict[Transport, AbstractTransport] | None = None) -> None:
        self._overrides: dict[Transport, AbstractTransport] = overrides or {}
        self._cache: dict[Transport, AbstractTransport] = {}

    def get(self, transport_type: Transport, **kwargs: Any) -> AbstractTransport:
        override = self._overrides.get(transport_type)
        if override is not None:
            return override
        cached = self._cache.get(transport_type)
        if cached is not None:
            return cached
        transport = self._create(transport_type, **kwargs)
        self._cache[transport_type] = transport
        return transport

    def _create(self, transport_type: Transport, **kwargs: Any) -> AbstractTransport:
        timeout = kwargs.get("timeout_ms", 30000)
        retries = kwargs.get("max_retries", 0)
        if transport_type in {Transport.HTTP, Transport.HTTPS, Transport.HTTP2}:
            return HTTPTransport(timeout_ms=timeout, max_retries=retries)
        if transport_type == Transport.GRPC:
            return GRPCTransport(max_retries=retries)
        if transport_type == Transport.AMQP:
            return AMQPTransport(request_timeout_ms=timeout, max_retries=retries)
        if transport_type == Transport.KAFKA:
            return KafkaTransport(request_timeout_ms=timeout)
        raise RuntimeError(f"Unsupported transport '{transport_type.value}'")

    async def close_all(self) -> None:
        for transport in self._cache.values():
            await transport.close()
        self._cache.clear()
