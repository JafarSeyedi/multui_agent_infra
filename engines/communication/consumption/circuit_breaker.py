"""Circuit breaker implementation for communication calls."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from dataclasses import field
from typing import Awaitable, Callable


class CircuitState:
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitConfig:
    failure_threshold: int = 5
    recovery_timeout_ms: int = 30000
    half_open_max_calls: int = 1


class CircuitBreaker:
    """Simplified production-grade circuit breaker with async support."""

    def __init__(self, config: CircuitConfig | None = None) -> None:
        self.config = config or CircuitConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self._opened_at: float | None = None
        self._half_open_calls = 0
        self._lock = asyncio.Lock()

    async def execute(self, func: Callable[[], Awaitable[object]]) -> object:
        if not await self._allow_request():
            raise RuntimeError("Circuit breaker is open")

        try:
            result = await func()
            await self._on_success()
            return result
        except Exception:
            await self._on_failure()
            raise

    async def _allow_request(self) -> bool:
        async with self._lock:
            if self.state == CircuitState.CLOSED:
                return True
            if self.state == CircuitState.OPEN:
                if self._opened_at is None:
                    self._set_open()
                    return False
                if (time.monotonic() - self._opened_at) * 1000 >= self.config.recovery_timeout_ms:
                    self.state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    return True
                return False
            # HALF_OPEN
            if self._half_open_calls >= self.config.half_open_max_calls:
                return False
            self._half_open_calls += 1
            return True

    async def _on_success(self) -> None:
        async with self._lock:
            self.failure_count = 0
            self.state = CircuitState.CLOSED
            self._half_open_calls = 0
            self._opened_at = None

    async def _on_failure(self) -> None:
        async with self._lock:
            self.failure_count += 1
            if self.failure_count >= self.config.failure_threshold:
                self._set_open()

    def _set_open(self) -> None:
        self.state = CircuitState.OPEN
        self._opened_at = time.monotonic()

    @property
    def is_open(self) -> bool:
        return self.state == CircuitState.OPEN

    @property
    def is_closed(self) -> bool:
        return self.state == CircuitState.CLOSED

    def snapshot(self) -> dict[str, object]:
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "opened_at": None if self._opened_at is None else self._opened_at,
            "half_open_calls": self._half_open_calls,
        }


@dataclass
class CircuitBreakerRegistry:
    """Keep one breaker per operation for cross-cutting protection."""

    defaults: CircuitConfig = field(default_factory=CircuitConfig)
    breakers: dict[str, CircuitBreaker] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.breakers = self.breakers or {}

    def get(self, operation_id: str) -> CircuitBreaker:
        if operation_id not in self.breakers:
            self.breakers[operation_id] = CircuitBreaker(self.defaults)
        return self.breakers[operation_id]
