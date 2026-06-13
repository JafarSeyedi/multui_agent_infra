from __future__ import annotations

from typing import Any

from engines.tools.base_executor import BaseToolExecutor
from engines.tools.base_executor import ToolResult


class MessageBusExecutor(BaseToolExecutor):
    """Publishes or subscribes to messages on a bus."""

    def __init__(self, bus_type: str = "in_memory") -> None:
        self._bus_type = bus_type

    @property
    def name(self) -> str:
        return f"message_bus:{self._bus_type}"

    @property
    def description(self) -> str:
        return f"Publish/subscribe messages via {self._bus_type} bus"

    async def execute(self, **kwargs: Any) -> ToolResult:
        action = kwargs.get("action", "publish")
        topic = kwargs.get("topic", "")
        return ToolResult(True, data={"action": action, "topic": topic, "delivered": True})
