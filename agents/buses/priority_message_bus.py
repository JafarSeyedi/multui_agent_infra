# پیام‌ها بر اساس اولویت پردازش می‌شوند، نه FIFO.

# agents/buses/priority_message_bus.py
import asyncio
import heapq
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List
from .base import MessageBus, HandlerType
from config.models.system.interaction_models import AgentMessage

logger = logging.getLogger(__name__)


@dataclass(order=True)
class PrioritizedMessage:
    priority: int
    message: Any = field(compare=False)


class PriorityMessageBus(MessageBus):
    """Priority-based message bus."""

    def __init__(self) -> None:
        self._queue: List[PrioritizedMessage] = []
        self._subscribers: Dict[str, List[HandlerType]] = {}
        self._lock = asyncio.Lock()
        self._processor_task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        self._running = True
        self._processor_task = asyncio.create_task(self._process())

    async def stop(self) -> None:
        self._running = False
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass

    async def subscribe(self, recipient: str, handler: HandlerType) -> None:
        async with self._lock:
            self._subscribers.setdefault(recipient, []).append(handler)

    async def unsubscribe(self, recipient: str, handler: HandlerType) -> None:
        async with self._lock:
            try:
                self._subscribers[recipient].remove(handler)
                if not self._subscribers[recipient]:
                    del self._subscribers[recipient]
            except (ValueError, KeyError):
                pass

    async def publish(self, message: AgentMessage, priority: int = 5) -> None:
        async with self._lock:
            heapq.heappush(self._queue, PrioritizedMessage(priority, message))

    async def _process(self) -> None:
        while self._running:
            async with self._lock:
                if not self._queue:
                    await asyncio.sleep(0.01)
                    continue
                item = heapq.heappop(self._queue)

            handlers = self._subscribers.get(item.message.recipient, [])
            await asyncio.gather(*[h(item.message) for h in handlers], return_exceptions=True)
