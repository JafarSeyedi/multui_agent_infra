"""Timer support for execution components.

Aligned with OSDM TimerEventDefinition semantics: date, timeCycle, timeDuration.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable, Any
from uuid import uuid4

from ..utils.time_utils import parse_duration, utc_now


@dataclass(frozen=True)
class TimerHandle:
    timer_id: str
    name: str
    callback: Callable[[], None]
    deadline: datetime
    state: str = "pending"
    osdm_timer_definition: Any = None


@dataclass
class OsDmTimerDefinition:
    """OSDM timer definition adapter for duration/date/cycle timers."""
    timer_type: str  # "date", "cycle", "duration"
    time_date: datetime | None = None
    time_cycle: str | None = None
    time_duration: str | float | int | None = None

    @classmethod
    def from_duration(cls, duration: str | int | float | timedelta) -> "OsDmTimerDefinition":
        return cls(timer_type="duration", time_duration=duration)

    @classmethod
    def from_date(cls, date_value: datetime) -> "OsDmTimerDefinition":
        return cls(timer_type="date", time_date=date_value)

    def calculate_deadline(self, reference_time: datetime | None = None) -> datetime:
        ref = reference_time or utc_now()
        if self.timer_type == "duration":
            delta = parse_duration(self.time_duration) if self.time_duration else timedelta()
            return ref + delta
        if self.timer_type == "date":
            return self.time_date or ref
        return ref + timedelta(hours=1)


class TimerManager:
    """Wrapper around asyncio timers with deterministic identifiers."""

    def __init__(self) -> None:
        self._tasks: dict[str, asyncio.Task[None]] = {}

    def schedule(self, name: str, delay: str | int | float, callback: Callable[[], None]) -> str:
        timer_id = f"timer-{uuid4().hex}"
        delay_delta = parse_duration(delay)
        deadline = utc_now() + delay_delta

        async def _runner() -> None:
            await asyncio.sleep(delay_delta.total_seconds())
            callback()
            self._tasks.pop(timer_id, None)

        task = asyncio.create_task(_runner())
        self._tasks[timer_id] = task
        return timer_id

    def cancel(self, timer_id: str) -> bool:
        task = self._tasks.pop(timer_id, None)
        if task is None:
            return False
        task.cancel()
        return True

    async def shutdown(self) -> None:
        for task in list(self._tasks.values()):
            task.cancel()
        tasks = list(self._tasks.values())
        self._tasks.clear()
        await asyncio.gather(*tasks, return_exceptions=True)
