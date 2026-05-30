"""Manage SSDM message channels over generic broker transports."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ...document.models.ssdm_models import MessageBinding, Transport
from ..common.serialization.json_serializer import JSONSerializer
from ..common.transport.amqp_client import AMQPTransport
from ..common.transport.base import AbstractTransport, TransportRequest, TransportResponse
from ..common.transport.kafka_client import KafkaTransport


@dataclass
class ChannelRegistration:
    name: str
    binding: MessageBinding
    metadata: dict[str, Any] = field(default_factory=dict)


class MessageChannelManager:
    """Register channels and publish/consume through transport abstractions."""

    def __init__(self, *, transport_overrides: dict[Transport, AbstractTransport] | None = None) -> None:
        self.transport_overrides = transport_overrides or {}
        self.channels: dict[str, ChannelRegistration] = {}
        self._transports: dict[Transport, AbstractTransport] = {}
        self._serializer = JSONSerializer()

    def register(self, name: str, binding: MessageBinding, *, metadata: dict[str, Any] | None = None) -> None:
        self.channels[name] = ChannelRegistration(name=name, binding=binding, metadata=metadata or {})

    def get(self, name: str) -> ChannelRegistration | None:
        return self.channels.get(name)

    async def publish(
        self,
        channel_name: str,
        payload: Any,
        *,
        headers: dict[str, str] | None = None,
    ) -> TransportResponse:
        registration = self._require(channel_name)
        transport = self._transport_for(registration.binding.transport)
        request = TransportRequest(
            url=registration.binding.topic or registration.binding.queue or channel_name,
            method="PUBLISH",
            headers=headers or {},
            params=self._params_for_binding(registration.binding),
            body=payload,
        )
        return await transport.send(
            request,
            payload_serializer=self._serializer.serialize,
            content_type=self._serializer.content_type,
        )

    async def close(self) -> None:
        for transport in self._transports.values():
            await transport.close()
        self._transports.clear()

    def _require(self, channel_name: str) -> ChannelRegistration:
        registration = self.channels.get(channel_name)
        if registration is None:
            raise RuntimeError(f"Unknown message channel '{channel_name}'")
        return registration

    def _params_for_binding(self, binding: MessageBinding) -> dict[str, Any]:
        return {
            "topic": binding.topic,
            "queue": binding.queue,
            "group_id": binding.group_id,
            "routing_key": binding.routing_key,
            "reply_to": binding.reply_to,
        }

    def _transport_for(self, transport: Transport) -> AbstractTransport:
        override = self.transport_overrides.get(transport)
        if override is not None:
            return override
        cached = self._transports.get(transport)
        if cached is not None:
            return cached
        if transport == Transport.AMQP:
            selected: AbstractTransport = AMQPTransport()
        elif transport == Transport.KAFKA:
            selected = KafkaTransport()
        else:
            raise RuntimeError(f"Unsupported message transport '{transport.value}'")
        self._transports[transport] = selected
        return selected
