"""Message router for multi-agent runtime.

Supports addressing, routing, broadcast, and persistent delivery/audit.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from ..core.engine import OrchestrationEngine
from ..core.event_bus import Event, EventType
from ..core.instance import ProcessInstance


@dataclass
class AgentMessage:
    message_id: str = ""
    message_type: str = "inform"
    sender: str = ""
    receiver: str = ""
    content: Any = None
    correlation_id: str | None = None
    reply_to: str | None = None
    timestamp: str = ""
    protocol: str = ""
    performative: str = "inform"


@dataclass
class RoutingResult:
    message_id: str
    routed: bool = False
    target: str | None = None
    errors: list[str] = field(default_factory=list)


class MessageRouter:
    def __init__(self, orchestration_engine: OrchestrationEngine | None = None) -> None:
        self._engine = orchestration_engine
        self._message_log: list[AgentMessage] = []
        self._delivery_callbacks: dict[str, Any] = {}

    def route(
        self,
        message: AgentMessage,
        instance: ProcessInstance | None = None,
    ) -> RoutingResult:
        self._message_log.append(message)

        if not message.receiver:
            return RoutingResult(
                message_id=message.message_id,
                routed=False,
                errors=["No receiver specified"],
            )

        if self._engine is not None and instance:
            asyncio.ensure_future(
                self._engine.event_bus.publish(
                    Event(
                        type=EventType.MESSAGE_SENT,
                        data={
                            "message_id": message.message_id,
                            "sender": message.sender,
                            "receiver": message.receiver,
                            "type": message.message_type,
                            "protocol": message.protocol,
                        },
                    )
                )
            )

        return RoutingResult(
            message_id=message.message_id,
            routed=True,
            target=message.receiver,
        )

    def broadcast(
        self,
        message: AgentMessage,
        recipients: list[str],
        instance: ProcessInstance | None = None,
    ) -> list[RoutingResult]:
        results: list[RoutingResult] = []
        for recipient in recipients:
            msg = AgentMessage(
                message_id=f"{message.message_id}_{recipient}",
                message_type=message.message_type,
                sender=message.sender,
                receiver=recipient,
                content=message.content,
                correlation_id=message.correlation_id,
                protocol=message.protocol,
            )
            results.append(self.route(msg, instance))
        return results

    def get_message_log(
        self,
        sender: str | None = None,
        receiver: str | None = None,
    ) -> list[AgentMessage]:
        results = self._message_log
        if sender:
            results = [m for m in results if m.sender == sender]
        if receiver:
            results = [m for m in results if m.receiver == receiver]
        return results

    def clear_log(self) -> int:
        count = len(self._message_log)
        self._message_log.clear()
        return count
