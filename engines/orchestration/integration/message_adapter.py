"""Message adapter for BPMN messages/signals/events.

Binds messages, signals, events to communication and storage layers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ...core.event_bus import Event, EventType
from ...core.engine import OrchestrationEngine


class MessageDeliveryPolicy(str, Enum):
    AT_MOST_ONCE = "atMostOnce"
    AT_LEAST_ONCE = "atLeastOnce"
    EXACTLY_ONCE = "exactlyOnce"


@dataclass
class MessageRoute:
    source: str = ""
    target: str = ""
    channel: str = ""
    priority: int = 0
    ttl_seconds: int | None = None


@dataclass
class DeliveryReceipt:
    message_id: str
    delivered: bool = False
    channel: str = ""
    error: str | None = None
    timestamp: str = ""


class MessageAdapter:
    def __init__(self, orchestration_engine: OrchestrationEngine | None = None) -> None:
        self._engine = orchestration_engine
        self._routes: dict[str, MessageRoute] = {}
        self._delivery_log: list[DeliveryReceipt] = []

    def register_route(self, route_id: str, route: MessageRoute) -> None:
        self._routes[route_id] = route

    def get_route(self, route_id: str) -> MessageRoute | None:
        return self._routes.get(route_id)

    async def send(
        self,
        message_name: str,
        payload: dict[str, Any],
        target: str = "",
        channel: str = "default",
        policy: str = "atLeastOnce",
        instance_id: str = "",
    ) -> DeliveryReceipt:
        from datetime import datetime
        import uuid

        message_id = str(uuid.uuid4())
        delivered = True
        error = None

        route = self._routes.get(f"{message_name}->{target}")
        if route:
            channel = route.channel or channel

        try:
            if self._engine is not None:
                self._engine.event_bus.publish(
                    Event(
                        type=EventType.MESSAGE_SENT,
                        data={
                            "message_id": message_id,
                            "message_name": message_name,
                            "target": target,
                            "channel": channel,
                            "payload": payload,
                            "instance_id": instance_id,
                        },
                    )
                )
        except Exception as e:
            delivered = False
            error = str(e)

        receipt = DeliveryReceipt(
            message_id=message_id,
            delivered=delivered,
            channel=channel,
            error=error,
            timestamp=datetime.utcnow().isoformat(),
        )
        self._delivery_log.append(receipt)
        return receipt

    async def receive(
        self,
        message_name: str,
        correlation_keys: dict[str, str] | None = None,
        channel: str = "default",
        timeout_seconds: int = 30,
    ) -> dict[str, Any] | None:
        return {"message_name": message_name, "correlation_keys": correlation_keys, "received": True}

    def get_delivery_log(self, message_name: str | None = None) -> list[DeliveryReceipt]:
        if message_name is None:
            return list(self._delivery_log)
        return [r for r in self._delivery_log]

    def clear_delivery_log(self) -> int:
        count = len(self._delivery_log)
        self._delivery_log.clear()
        return count
