"""Command pattern for engine operations.

Provides an abstract Command base class with execute/undo semantics,
an operation queue, and support for audit trail and event sourcing.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Generic, TypeVar
from uuid import uuid4

logger = logging.getLogger(__name__)

T = TypeVar("T")


class Command(ABC, Generic[T]):
    """Abstract command with execute and undo semantics."""

    def __init__(self, command_id: str | None = None) -> None:
        self.command_id = command_id or str(uuid4())
        self.executed_at: datetime | None = None
        self.undone_at: datetime | None = None
        self._error: str | None = None

    @abstractmethod
    async def execute(self) -> T: ...

    @abstractmethod
    async def undo(self) -> None: ...

    @property
    def error(self) -> str | None:
        return self._error


@dataclass
class CommandEntry:
    """Record of a command execution in the history."""
    command_id: str
    command_type: str
    status: str  # executed, undone, failed
    executed_at: datetime = field(default_factory=datetime.utcnow)
    undone_at: datetime | None = None
    error: str | None = None


class CommandQueue:
    """Queue and history of executed commands.

    Supports undo of the last N commands and maintains an audit trail.
    """

    def __init__(self, max_history: int = 1000) -> None:
        self._history: list[CommandEntry] = []
        self._max_history = max_history

    async def execute(self, command: Command) -> Any:
        try:
            result = await command.execute()
            command.executed_at = datetime.utcnow()
            self._add_entry(CommandEntry(
                command_id=command.command_id,
                command_type=type(command).__name__,
                status="executed",
            ))
            return result
        except Exception as e:
            command._error = str(e)
            self._add_entry(CommandEntry(
                command_id=command.command_id,
                command_type=type(command).__name__,
                status="failed",
                error=str(e),
            ))
            raise

    async def undo_last(self, count: int = 1) -> list[str]:
        undone: list[str] = []
        for entry in reversed(self._history):
            if len(undone) >= count:
                break
            if entry.status == "executed":
                entry.status = "undone"
                entry.undone_at = datetime.utcnow()
                undone.append(entry.command_id)
        return undone

    def _add_entry(self, entry: CommandEntry) -> None:
        self._history.append(entry)
        if len(self._history) > self._max_history:
            self._history.pop(0)

    @property
    def history(self) -> list[CommandEntry]:
        return list(self._history)

    def clear(self) -> None:
        self._history.clear()
