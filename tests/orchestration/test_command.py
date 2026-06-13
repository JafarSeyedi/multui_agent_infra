"""Tests for Command pattern."""

from __future__ import annotations

import pytest

from engines.orchestration.command import Command, CommandHistory, CommandInvoker


class AddCommand(Command[int]):
    def __init__(self, a: int, b: int) -> None:
        super().__init__()
        self._a = a
        self._b = b
        self._result: int | None = None

    @property
    def description(self) -> str:
        return f"Add {self._a} + {self._b}"

    async def execute(self) -> int:
        self._result = self._a + self._b
        return self._result

    async def undo(self) -> None:
        self._result = None


@pytest.mark.asyncio
async def test_command_execute():
    cmd = AddCommand(2, 3)
    invoker = CommandInvoker()
    result = await invoker.execute(cmd)
    assert result == 5
    assert cmd.record.status == "completed"
    assert cmd.record.executed_at is not None


@pytest.mark.asyncio
async def test_command_undo():
    cmd = AddCommand(2, 3)
    invoker = CommandInvoker()
    await invoker.execute(cmd)
    await invoker.undo_last()
    assert cmd.record.status == "undone"
    assert cmd.record.undone_at is not None


@pytest.mark.asyncio
async def test_command_history():
    invoker = CommandInvoker()
    await invoker.execute(AddCommand(1, 1))
    await invoker.execute(AddCommand(2, 2))
    assert len(invoker.history) == 2
    assert invoker.history.last is not None
    assert invoker.history.last.description == "Add 2 + 2"


@pytest.mark.asyncio
async def test_command_failure():
    class FailCommand(Command[int]):
        @property
        def description(self) -> str:
            return "Fails always"

        async def execute(self) -> int:
            raise ValueError("Expected failure")

    cmd = FailCommand()
    invoker = CommandInvoker()
    with pytest.raises(ValueError, match="Expected failure"):
        await invoker.execute(cmd)
    assert cmd.record.status == "failed"
    assert cmd.record.error is not None
