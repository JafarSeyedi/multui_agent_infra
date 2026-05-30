"""Message ingress/egress adapters with lightweight buffering."""

from __future__ import annotations

from dataclasses import dataclass
from queue import Queue
from typing import Any


@dataclass(frozen=True)
class MessageAdapter:
    """Minimal in-memory message adapter."""

    queue: Queue = Queue()

    def publish(self, payload: Any) -> None:
        self.queue.put(payload)

    def receive(self, *, block: bool = False) -> Any:
        return self.queue.get(block=block, timeout=None if block else 0)

    def drain(self, max_messages: int = 100) -> list[Any]:
        items: list[Any] = []
        while len(items) < max_messages and not self.queue.empty():
            items.append(self.queue.get())
        return items
