# engines/events/backends/in_memory/in_memory_events.py
from __future__ import annotations

from typing import Any, Optional

from ...models.events_models import EventRecord
from ...plugin import IEventProducer, IEventConsumer


class InMemoryEventProducer(IEventProducer):
    name = "in_memory"

    def __init__(self, bus: dict[str, list[EventRecord]]) -> None:
        self._bus = bus

    async def publish(self, topic: str, event: dict[str, Any]) -> None:
        if topic not in self._bus:
            self._bus[topic] = []
        self._bus[topic].append(EventRecord(topic=topic, data=event))


class InMemoryEventConsumer(IEventConsumer):
    name = "in_memory"

    def __init__(self, bus: dict[str, list[EventRecord]]) -> None:
        self._bus = bus
        self._subscriptions: set[str] = set()

    async def subscribe(self, topic: str, handler_name: str) -> None:
        self._subscriptions.add(topic)

    async def consume(self, topic: str) -> Optional[dict[str, Any]]:
        if topic not in self._bus or not self._bus[topic]:
            return None
        return self._bus[topic].pop(0).data
