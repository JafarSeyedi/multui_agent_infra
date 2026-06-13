"""Circuit breaker and retry mechanism for orchestration runtime.

Implements circuit breaker pattern (Kestra/Orch8 style) and configurable
retry with exponential backoff (Camunda/Flowable style).
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class RetryConfig:
    max_attempts: int = 3
    initial_delay_ms: int = 1000
    backoff_multiplier: float = 2.0
    max_delay_ms: int = 60000
    jitter_factor: float = 0.1
    retry_on_exceptions: tuple[type[Exception], ...] = (Exception,)
    abort_on_exceptions: tuple[type[Exception], ...] = ()

    def get_delay(self, attempt: int) -> float:
        import random
        delay = self.initial_delay_ms * (self.backoff_multiplier ** attempt)
        delay = min(delay, self.max_delay_ms)
        jitter = delay * self.jitter_factor * (random.random() - 0.5)
        return max(0, (delay + jitter) / 1000.0)


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    success_threshold: int = 3
    open_duration_seconds: int = 60
    half_open_max_calls: int = 1
    monitor_window_seconds: int = 300


@dataclass
class RetryContext:
    attempt: int = 0
    max_attempts: int = 3
    last_error: str | None = None
    total_delay_ms: float = 0.0
    retriable: bool = True


@dataclass
class CircuitBreaker:
    name: str
    config: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    state: str = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float = 0.0
    half_open_calls: int = 0
    _state_obj: Any = None  # Will be lazily initialized

    def __post_init__(self) -> None:
        from .circuit_states import state_for
        self._state_obj = state_for(self.state)

    def can_execute(self) -> bool:
        return self._state_obj.can_execute(self)

    def record_success(self) -> None:
        self._state_obj.record_success(self)

    def record_failure(self) -> None:
        self._state_obj.record_failure(self)


class RetryHandler:
    def __init__(self, config: RetryConfig | None = None) -> None:
        self._config = config or RetryConfig()

    async def execute_with_retry(
        self,
        operation: Callable[..., Any],
        *args: Any,
        retry_config: RetryConfig | None = None,
        **kwargs: Any,
    ) -> Any:
        config = retry_config or self._config
        last_error: Exception | None = None

        for attempt in range(config.max_attempts + 1):
            try:
                if kwargs:
                    return await operation(*args, **kwargs)
                return await operation(*args)
            except tuple(config.abort_on_exceptions) as _e:
                raise
            except tuple(config.retry_on_exceptions) as _e:
                last_error = _e
                if attempt >= config.max_attempts:
                    break
                delay = config.get_delay(attempt)
                logger.warning("Retry %d/%d after %.1fs error: %s",
                               attempt + 1, config.max_attempts, delay, str(_e))
                import asyncio
                await asyncio.sleep(delay)

        if last_error is None:
            raise RuntimeError("Operation failed with no captured error")
        raise last_error

    def execute_with_retry_sync(
        self,
        operation: Callable[..., Any],
        *args: Any,
        retry_config: RetryConfig | None = None,
        **kwargs: Any,
    ) -> Any:
        config = retry_config or self._config
        last_error: Exception | None = None

        for attempt in range(config.max_attempts + 1):
            try:
                return operation(*args, **kwargs)
            except tuple(config.abort_on_exceptions) as _e:
                raise
            except tuple(config.retry_on_exceptions) as _e:
                last_error = _e
                if attempt >= config.max_attempts:
                    break
                delay = config.get_delay(attempt)
                logger.warning("Retry %d/%d after %.1fs error: %s",
                               attempt + 1, config.max_attempts, delay, str(_e))
                time.sleep(delay)

        if last_error is None:
            raise RuntimeError("Operation failed with no captured error")
        raise last_error


class CircuitBreakerRegistry:
    def __init__(self) -> None:
        self._breakers: dict[str, CircuitBreaker] = {}

    def get_or_create(
        self,
        name: str,
        config: CircuitBreakerConfig | None = None,
    ) -> CircuitBreaker:
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(
                name=name,
                config=config or CircuitBreakerConfig(),
            )
        return self._breakers[name]

    def get_breaker(self, name: str) -> CircuitBreaker | None:
        return self._breakers.get(name)

    def list_breakers(self) -> list[CircuitBreaker]:
        return list(self._breakers.values())

    def remove_breaker(self, name: str) -> bool:
        return self._breakers.pop(name, None) is not None
