"""State pattern — circuit breaker states."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)


class CBState:
    """Base circuit breaker state."""

    def can_execute(self, cb: CircuitBreaker) -> bool:
        return False

    def record_success(self, cb: CircuitBreaker) -> None:
        cb.failure_count = max(0, cb.failure_count - 1)

    def record_failure(self, cb: CircuitBreaker) -> None:
        cb.failure_count += 1
        cb.last_failure_time = time.time()

    @property
    def name(self) -> str:
        return "unknown"


class ClosedState(CBState):
    def can_execute(self, cb: CircuitBreaker) -> bool:
        return True

    def record_success(self, cb: CircuitBreaker) -> None:
        super().record_success(cb)

    def record_failure(self, cb: CircuitBreaker) -> None:
        super().record_failure(cb)
        if cb.failure_count >= cb.config.failure_threshold:
            cb._state_obj = OpenState()
            cb.state = "open"
            logger.warning("Circuit breaker '%s' OPENED after %d failures", cb.name, cb.failure_count)

    @property
    def name(self) -> str:
        return "closed"


class OpenState(CBState):
    def can_execute(self, cb: CircuitBreaker) -> bool:
        if time.time() - cb.last_failure_time >= cb.config.open_duration_seconds:
            cb._state_obj = HalfOpenState()
            cb.state = "half_open"
            cb.half_open_calls = 0
            logger.info("Circuit breaker '%s' moved to HALF_OPEN", cb.name)
            return True
        return False

    @property
    def name(self) -> str:
        return "open"


class HalfOpenState(CBState):
    def can_execute(self, cb: CircuitBreaker) -> bool:
        return cb.half_open_calls < cb.config.half_open_max_calls

    def record_success(self, cb: CircuitBreaker) -> None:
        cb.success_count += 1
        cb.half_open_calls += 1
        if cb.success_count >= cb.config.success_threshold:
            cb._state_obj = ClosedState()
            cb.state = "closed"
            cb.failure_count = 0
            cb.success_count = 0
            logger.info("Circuit breaker '%s' CLOSED", cb.name)

    def record_failure(self, cb: CircuitBreaker) -> None:
        super().record_failure(cb)
        cb._state_obj = OpenState()
        cb.state = "open"
        cb.half_open_calls = 0
        logger.warning("Circuit breaker '%s' re-OPENED from HALF_OPEN", cb.name)

    @property
    def name(self) -> str:
        return "half_open"


def state_for(state_str: str) -> CBState:
    mapping = {"closed": ClosedState(), "open": OpenState(), "half_open": HalfOpenState()}
    return mapping.get(state_str, ClosedState())
