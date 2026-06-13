"""Pluggable health checks for runtime dependencies."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from collections.abc import Callable


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass(frozen=True)
class HealthCheckResult:
    name: str
    status: HealthStatus
    message: str | None = None


CheckFn = Callable[[], bool]


class HealthMonitor:
    """Evaluate named check functions and aggregate state."""

    def __init__(self) -> None:
        self._checks: dict[str, CheckFn] = {}

    def register(self, name: str, check: CheckFn) -> None:
        self._checks[name] = check

    def unregister(self, name: str) -> None:
        self._checks.pop(name, None)

    def run(self) -> list[HealthCheckResult]:
        results: list[HealthCheckResult] = []
        for name, check in self._checks.items():
            try:
                passed = check()
                status = HealthStatus.HEALTHY if passed else HealthStatus.UNHEALTHY
                results.append(HealthCheckResult(name=name, status=status))
            except Exception as exc:
                results.append(HealthCheckResult(name=name, status=HealthStatus.UNHEALTHY, message=str(exc)))
        return results

    def all_healthy(self) -> bool:
        return all(item.status == HealthStatus.HEALTHY for item in self.run())
