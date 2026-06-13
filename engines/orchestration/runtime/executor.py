"""Synchronous/async execution wrapper with bounded error handling."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any
from collections.abc import Awaitable, Callable


class RuntimeTaskError(RuntimeError):
    """Raised when runtime task invocation fails."""


@dataclass(frozen=True)
class ExecutionOutcome:
    """Outcome of a runtime execution."""

    result: Any
    success: bool
    error: Exception | None = None


class RuntimeExecutor:
    """Run callables with consistent async/sync execution contract."""

    async def run(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> ExecutionOutcome:
        try:
            if asyncio.iscoroutinefunction(func):
                value = await func(*args, **kwargs)
            else:
                value = func(*args, **kwargs)
            return ExecutionOutcome(result=value, success=True)
        except Exception as error:  # pragma: no cover - intentionally broad boundary
            return ExecutionOutcome(result=None, success=False, error=error)

    async def run_async_or_sync(self, fn: Callable[..., Any]) -> Any:
        if asyncio.iscoroutinefunction(fn):
            return await fn()
        maybe = fn()
        if isinstance(maybe, Awaitable):
            return await maybe
        return maybe
