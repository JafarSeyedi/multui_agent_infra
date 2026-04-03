from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Awaitable, Callable, Dict, List

from config.models.system.interaction_models import AgentMessage


MessageHandler = Callable[[AgentMessage], Awaitable[None]]


class InMemoryMessageBus:
    """Simple async agent-to-agent bus for local orchestration and tests."""

    def __init__(self):
        self._subscribers: Dict[str, List[MessageHandler]] = defaultdict(list)

    def subscribe(self, recipient: str, handler: MessageHandler) -> None:
        self._subscribers[recipient].append(handler)

    async def publish(self, message: AgentMessage) -> None:
        handlers = list(self._subscribers.get(message.recipient, []))
        if not handlers:
            return
        await asyncio.gather(*(handler(message) for handler in handlers))
