"""Rate limiting for orchestration runtime.

Implements per-resource sliding window rate limiting per Kestra/Orch8 patterns.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from threading import Lock
from typing import Any


@dataclass
class RateLimitConfig:
    resource_name: str
    max_requests: int = 100
    window_seconds: int = 60
    burst_size: int | None = None

    def __post_init__(self) -> None:
        if self.burst_size is None:
            self.burst_size = self.max_requests


@dataclass
class RateLimitStatus:
    resource_name: str
    allowed: bool
    remaining: int
    reset_time: float
    retry_after_seconds: float = 0.0
    current_count: int = 0
    max_requests: int = 0
    window_seconds: int = 0


@dataclass
class _WindowState:
    requests: list[float] = field(default_factory=list)


class RateLimiter:
    def __init__(self) -> None:
        self._configs: dict[str, RateLimitConfig] = {}
        self._windows: dict[str, _WindowState] = {}
        self._lock = Lock()

    def configure(self, config: RateLimitConfig) -> None:
        self._configs[config.resource_name] = config
        if config.resource_name not in self._windows:
            self._windows[config.resource_name] = _WindowState()

    def check(self, resource_name: str) -> RateLimitStatus:
        config = self._configs.get(resource_name)
        if config is None:
            return RateLimitStatus(
                resource_name=resource_name, allowed=True, remaining=999999,
                reset_time=time.time() + 60, max_requests=999999, window_seconds=60,
            )

        with self._lock:
            state = self._windows.setdefault(resource_name, _WindowState())
            now = time.time()
            cutoff = now - config.window_seconds
            state.requests = [t for t in state.requests if t > cutoff]
            current = len(state.requests)

            if current >= config.max_requests:
                oldest = min(state.requests) if state.requests else now
                reset_time = oldest + config.window_seconds
                return RateLimitStatus(
                    resource_name=resource_name, allowed=False, remaining=0,
                    reset_time=reset_time, retry_after_seconds=max(0, reset_time - now),
                    current_count=current, max_requests=config.max_requests,
                    window_seconds=config.window_seconds,
                )

            state.requests.append(now)
            remaining = config.max_requests - current - 1
            reset_time = now + config.window_seconds

            return RateLimitStatus(
                resource_name=resource_name, allowed=True, remaining=remaining,
                reset_time=reset_time, current_count=current + 1,
                max_requests=config.max_requests, window_seconds=config.window_seconds,
            )

    def peek(self, resource_name: str) -> RateLimitStatus:
        config = self._configs.get(resource_name)
        if config is None:
            return RateLimitStatus(
                resource_name=resource_name, allowed=True, remaining=999999,
                reset_time=time.time() + 60, max_requests=999999, window_seconds=60,
            )

        with self._lock:
            state = self._windows.get(resource_name, _WindowState())
            now = time.time()
            cutoff = now - config.window_seconds
            active = len([t for t in state.requests if t > cutoff])

            if active >= config.max_requests:
                oldest = min(state.requests) if state.requests else now
                return RateLimitStatus(
                    resource_name=resource_name, allowed=False, remaining=0,
                    reset_time=oldest + config.window_seconds,
                    retry_after_seconds=max(0, oldest + config.window_seconds - now),
                    current_count=active, max_requests=config.max_requests,
                    window_seconds=config.window_seconds,
                )

            return RateLimitStatus(
                resource_name=resource_name, allowed=True,
                remaining=config.max_requests - active,
                reset_time=now + config.window_seconds,
                current_count=active, max_requests=config.max_requests,
                window_seconds=config.window_seconds,
            )

    def reset(self, resource_name: str) -> bool:
        with self._lock:
            state = self._windows.get(resource_name)
            if state:
                state.requests.clear()
                return True
            return False

    def get_status(self, resource_name: str) -> RateLimitStatus:
        return self.peek(resource_name)

    def list_resources(self) -> list[str]:
        return list(self._configs.keys())

    def remove_config(self, resource_name: str) -> bool:
        with self._lock:
            self._configs.pop(resource_name, None)
            self._windows.pop(resource_name, None)
            return True
