"""Timer support for execution components."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Callable
from uuid import uuid4

from ..utils.time_utils import parse_duration, utc_now


@dataclass(frozen=True)
class TimerHandle:
    timer_id: str
    name: str
    callback: Callable[[], None]
    deadline: datetime


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
