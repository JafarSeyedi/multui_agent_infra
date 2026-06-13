"""Execution decorators for cross-cutting concerns.

Follows the Decorator pattern: each decorator wraps an executor
callable and adds behavior before/after/around execution.
"""

from __future__ import annotations

import asyncio
import functools
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, TypeVar, cast
from collections.abc import Awaitable, Callable

from ..._types import Metadata

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


class ExecutionDecorator(ABC):
    """Base decorator for wrapping executor calls."""

    def __init__(self, inner: ExecutionDecorator | Callable | None = None) -> None:
        self._inner = inner

    @abstractmethod
    async def execute(self, context: Metadata) -> Any:
        ...

    def decorate(self, fn: F) -> F:
        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:  # duck-typed
            context = {"fn": fn, "args": args, "kwargs": kwargs}
            return await self.execute(context)
        return cast(F, wrapper)


class LoggingDecorator(ExecutionDecorator):
    """Logs entry/exit and duration of execution."""

    async def execute(self, context: Metadata) -> Any:
        fn = context["fn"]
        fn_name = getattr(fn, "__qualname__", str(fn))
        logger.info("Entering %s", fn_name)
        start = time.monotonic()
        try:
            inner = cast(ExecutionDecorator, self._inner) if isinstance(self._inner, ExecutionDecorator) else None
            if inner:
                result = await inner.execute(context)
            else:
                result = await fn(*context["args"], **context["kwargs"])
            elapsed = time.monotonic() - start
            logger.info("Exiting %s (%.3fs)", fn_name, elapsed)
            return result
        except Exception as exc:
            elapsed = time.monotonic() - start
            logger.error("%s failed after %.3fs: %s", fn_name, elapsed, exc)
            raise


class TimingDecorator(ExecutionDecorator):
    """Records execution time metrics."""

    def __init__(
        self,
        inner: ExecutionDecorator | Callable | None = None,
        *,
        metrics: dict[str, list[float]] | None = None,
    ) -> None:
        super().__init__(inner)
        self._metrics: dict[str, list[float]] = {} if metrics is None else metrics

    async def execute(self, context: Metadata) -> Any:
        fn = context["fn"]
        fn_name = getattr(fn, "__qualname__", str(fn))
        start = time.monotonic()
        try:
            inner = cast(ExecutionDecorator, self._inner) if isinstance(self._inner, ExecutionDecorator) else None
            if inner:
                result = await inner.execute(context)
            else:
                result = await fn(*context["args"], **context["kwargs"])
            return result
        finally:
            elapsed = time.monotonic() - start
            self._metrics.setdefault(fn_name, []).append(elapsed)

    def average_time(self, fn_name: str) -> float:
        times = self._metrics.get(fn_name, [])
        return sum(times) / len(times) if times else 0.0


class RetryDecorator(ExecutionDecorator):
    """Retries execution on failure with backoff."""

    def __init__(
        self,
        inner: ExecutionDecorator | Callable | None = None,
        *,
        max_retries: int = 3,
        base_delay: float = 0.1,
        max_delay: float = 5.0,
        retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
    ) -> None:
        super().__init__(inner)
        self._max_retries = max_retries
        self._base_delay = base_delay
        self._max_delay = max_delay
        self._retryable_exceptions = retryable_exceptions

    async def execute(self, context: Metadata) -> Any:
        fn = context["fn"]
        fn_name = getattr(fn, "__qualname__", str(fn))
        last_exc: Exception | None = None
        for attempt in range(1, self._max_retries + 1):
            try:
                inner = cast(ExecutionDecorator, self._inner) if isinstance(self._inner, ExecutionDecorator) else None
                if inner:
                    return await inner.execute(context)
                return await fn(*context["args"], **context["kwargs"])
            except self._retryable_exceptions as exc:
                last_exc = exc
                if attempt < self._max_retries:
                    delay = min(self._base_delay * (2 ** (attempt - 1)), self._max_delay)
                    logger.warning("Retry %d/%d for %s after %.3fs: %s", attempt, self._max_retries, fn_name, delay, exc)
                    await asyncio.sleep(delay)
        if last_exc is not None:
            raise last_exc


class CircuitBreakerDecorator(ExecutionDecorator):
    """Prevents execution when failure threshold is exceeded."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

    def __init__(
        self,
        inner: ExecutionDecorator | Callable | None = None,
        *,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
    ) -> None:
        super().__init__(inner)
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._state = self.CLOSED
        self._failure_count = 0
        self._last_failure_time: float | None = None

    async def execute(self, context: Metadata) -> Any:
        fn_name = getattr(context["fn"], "__qualname__", str(context["fn"]))
        if self._state == self.OPEN:
            if self._last_failure_time and (time.monotonic() - self._last_failure_time) >= self._recovery_timeout:
                logger.info("Circuit breaker half-opening for %s", fn_name)
                self._state = self.HALF_OPEN
            else:
                raise RuntimeError(f"Circuit breaker is OPEN for {fn_name}")
        try:
            inner = cast(ExecutionDecorator, self._inner) if isinstance(self._inner, ExecutionDecorator) else None
            if inner:
                result = await inner.execute(context)
            else:
                result = await context["fn"](*context["args"], **context["kwargs"])
            if self._state == self.HALF_OPEN:
                logger.info("Circuit breaker closing for %s", fn_name)
                self._state = self.CLOSED
                self._failure_count = 0
            return result
        except Exception:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()
            if self._failure_count >= self._failure_threshold:
                logger.warning("Circuit breaker OPENING for %s (%d failures)", fn_name, self._failure_count)
                self._state = self.OPEN
            raise


class CompositeDecorator(ExecutionDecorator):
    """Chains multiple decorators into one execution pipeline.

    The first decorator in the list wraps the second, and so on,
    with the original callable as the innermost.
    """

    def __init__(self, decorators: list[ExecutionDecorator], inner: Callable | None = None) -> None:
        self._inner = self._chain(decorators, inner)
        super().__init__(inner)

    @staticmethod
    def _chain(decorators: list[ExecutionDecorator], innermost: Callable | None) -> ExecutionDecorator | Callable:
        if not decorators:
            return innermost if innermost else _noop_executor
        current: ExecutionDecorator | Callable = innermost if innermost else _noop_executor
        for decorator in reversed(decorators):
            decorator._inner = current
            current = decorator
        return current

    async def execute(self, context: Metadata) -> Any:
        inner = self._inner
        if isinstance(inner, ExecutionDecorator):
            return await inner.execute(context)
        assert inner is not None
        return await inner(context)


async def _noop_executor(context: Metadata) -> Any:
    return None
