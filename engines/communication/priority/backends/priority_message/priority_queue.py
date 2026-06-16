# engines/communication/priority/backends/priority_message/priority_queue.py
from __future__ import annotations

import heapq
from typing import Optional

from ....models.communication_models import ChannelMessage, MessagePriority
from ...plugin import PriorityChannel


class InMemoryPriorityQueue(PriorityChannel):
    """In-memory priority queue for testing."""

    name = "in_memory"

    def __init__(self) -> None:
        self._queue: list[tuple[int, int, ChannelMessage]] = []
        self._counter = 0
        self._handler = None
        self._started = False

    async def enqueue(self, message: ChannelMessage, priority: MessagePriority | None = None) -> None:
        p = (priority or message.priority).value
        heapq.heappush(self._queue, (-p, self._counter, message))
        self._counter += 1

    async def send(self, message: ChannelMessage) -> None:
        await self.enqueue(message)

    async def receive(self, handler) -> None:
        self._handler = handler

    async def dequeue(self) -> Optional[ChannelMessage]:
        if not self._queue:
            return None
        _, _, message = heapq.heappop(self._queue)
        return message

    async def start(self) -> None:
        self._started = True

    async def stop(self) -> None:
        self._queue.clear()
        self._handler = None
        self._started = False
