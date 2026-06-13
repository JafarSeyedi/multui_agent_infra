from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Any

from .._types import VariableValue


class ToolResult:
    def __init__(self, success: bool, data: VariableValue = None, error: str | None = None) -> None:
        self.success = success
        self.data = data
        self.error = error

    def __repr__(self) -> str:
        if self.success:
            return f"ToolResult(success=True, data={self.data!r})"
        return f"ToolResult(success=False, error={self.error!r})"


class BaseToolExecutor(ABC):
    """Strategy pattern — common interface for all tool executors."""

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        ...
