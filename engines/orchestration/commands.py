"""Concrete Command implementations for orchestration operations."""

from __future__ import annotations

import logging
from typing import Any

from .command import Command
from .core.event_bus import Event, EventType
from .core.instance import InstanceState

logger = logging.getLogger(__name__)


class StartInstanceCommand(Command[Any]):
    """Start a process instance."""

    def __init__(self, instance_service: Any, definition: Any, **kwargs: Any) -> None:
        super().__init__()
        self._instance_service = instance_service
        self._definition = definition
        self._kwargs = kwargs
        self._instance_id: str | None = None

    @property
    def description(self) -> str:
        return f"Start instance of {self._definition.key} (v{self._definition.version})"

    async def execute(self) -> Any:
        instance = await self._instance_service.start_instance(self._definition, **self._kwargs)
        self._instance_id = instance.id
        return instance

    async def undo(self) -> None:
        if self._instance_id:
            await self._instance_service.update_instance_state(
                None, InstanceState.TERMINATED, reason="Command undo"
            )


class SuspendInstanceCommand(Command[Any]):
    """Suspend a running process instance."""

    def __init__(self, instance_service: Any, instance: Any, reason: str | None = None) -> None:
        super().__init__()
        self._instance_service = instance_service
        self._instance = instance
        self._reason = reason

    @property
    def description(self) -> str:
        return f"Suspend instance {self._instance.id}"

    async def execute(self) -> Any:
        return await self._instance_service.update_instance_state(
            self._instance, InstanceState.SUSPENDED, reason=self._reason
        )


class ResumeInstanceCommand(Command[Any]):
    """Resume a suspended process instance."""

    def __init__(self, instance_service: Any, instance: Any) -> None:
        super().__init__()
        self._instance_service = instance_service
        self._instance = instance

    @property
    def description(self) -> str:
        return f"Resume instance {self._instance.id}"

    async def execute(self) -> Any:
        return await self._instance_service.update_instance_state(
            self._instance, InstanceState.ACTIVE
        )


class TerminateInstanceCommand(Command[Any]):
    """Terminate a process instance."""

    def __init__(self, instance_service: Any, instance: Any, reason: str | None = None) -> None:
        super().__init__()
        self._instance_service = instance_service
        self._instance = instance
        self._reason = reason

    @property
    def description(self) -> str:
        return f"Terminate instance {self._instance.id}"

    async def execute(self) -> Any:
        return await self._instance_service.update_instance_state(
            self._instance, InstanceState.TERMINATED, reason=self._reason
        )


class ThrowSignalCommand(Command[Any]):
    """Throw a BPMN signal event."""

    def __init__(self, event_bus: Any, signal_name: str, data: dict[str, Any] | None = None) -> None:
        super().__init__()
        self._event_bus = event_bus
        self._signal_name = signal_name
        self._data = data or {}

    @property
    def description(self) -> str:
        return f"Throw signal: {self._signal_name}"

    async def execute(self) -> Any:
        await self._event_bus.publish(
            Event(
                type=EventType.SIGNAL_THROWN,
                data={"signal_name": self._signal_name, **self._data},
            )
        )
        return self._signal_name


class PublishMessageCommand(Command[Any]):
    """Correlate and deliver a BPMN message."""

    def __init__(self, event_bus: Any, correlation_engine: Any, message_name: str, payload: dict[str, Any]) -> None:
        super().__init__()
        self._event_bus = event_bus
        self._correlation_engine = correlation_engine
        self._message_name = message_name
        self._payload = payload

    @property
    def description(self) -> str:
        return f"Publish message: {self._message_name}"

    async def execute(self) -> Any:
        result = await self._correlation_engine.correlate_message(self._message_name, self._payload)
        await self._event_bus.publish(
            Event(
                type=EventType.MESSAGE_CORRELATED,
                data={"message_name": self._message_name, "correlated": result},
            )
        )
        return result
