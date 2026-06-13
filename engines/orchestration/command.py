"""Command pattern — encapsulate orchestration operations as command objects.

Supports execution, undo, queuing, and audit logging of commands
without coupling the invoker to the receiver.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Generic, TypeVar
from uuid import uuid4

TResult = TypeVar("TResult")

logger = logging.getLogger(__name__)


@dataclass
class CommandRecord:
    command_id: str
    command_name: str
    status: str  # pending, executing, completed, failed, undone
    created_at: datetime = field(default_factory=datetime.utcnow)
    executed_at: datetime | None = None
    undone_at: datetime | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class Command(ABC, Generic[TResult]):
    """Base command — encapsulate an operation and its inverse."""

    def __init__(self) -> None:
        self._record = CommandRecord(
            command_id=str(uuid4()),
            command_name=self.__class__.__name__,
            status="pending",
        )

    @property
    def record(self) -> CommandRecord:
        return self._record

    @abstractmethod
    async def execute(self) -> TResult:
        ...

    async def undo(self) -> None:
        raise RuntimeError(f"{self.__class__.__name__} does not support undo")

    @property
    @abstractmethod
    def description(self) -> str:
        ...


class CommandHistory:
    """Manages command execution history with undo support."""

    def __init__(self, max_size: int = 1000) -> None:
        self._commands: list[Command] = []
        self._max_size = max_size

    def push(self, command: Command) -> None:
        self._commands.append(command)
        if len(self._commands) > self._max_size:
            self._commands.pop(0)

    def pop(self) -> Command | None:
        return self._commands.pop() if self._commands else None

    @property
    def last(self) -> Command | None:
        return self._commands[-1] if self._commands else None

    @property
    def all(self) -> list[Command]:
        return list(self._commands)

    def clear(self) -> None:
        self._commands.clear()

    def __len__(self) -> int:
        return len(self._commands)


class CommandInvoker:
    """Invoker — executes commands and manages history."""

    def __init__(self, history: CommandHistory | None = None) -> None:
        self._history = history or CommandHistory()

    @property
    def history(self) -> CommandHistory:
        return self._history

    async def execute(self, command: Command) -> Any:
        command.record.status = "executing"
        try:
            result = await command.execute()
            command.record.status = "completed"
            command.record.executed_at = datetime.utcnow()
            self._history.push(command)
            return result
        except Exception as exc:
            command.record.status = "failed"
            command.record.error = str(exc)
            logger.exception("Command %s failed", command.__class__.__name__)
            raise

    async def undo_last(self) -> None:
        command = self._history.pop()
        if command is None:
            return None
        try:
            await command.undo()
            command.record.status = "undone"
            command.record.undone_at = datetime.utcnow()
        except RuntimeError:
            self._history.push(command)
            raise

    async def execute_batch(self, commands: list[Command]) -> list[Any]:
        results: list[Any] = []
        for cmd in commands:
            results.append(await self.execute(cmd))
        return results
