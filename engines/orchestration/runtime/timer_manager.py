"""Timer support for execution components.

Aligned with OSDM TimerEventDefinition semantics: date, timeCycle, timeDuration.
Creates timer jobs that fire events via the process executor when deadlines are reached.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from collections.abc import Callable
from uuid import uuid4

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..bpmn.models.bpmn_models import TimerEventDefinition, DueTimeDuration
from ..utils.time_utils import parse_duration, utc_now


logger = logging.getLogger(__name__)


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
    time_duration: str | float | int | timedelta | None = None

    @classmethod
    def from_duration(cls, duration: str | int | float | timedelta) -> OsDmTimerDefinition:
        return cls(timer_type="duration", time_duration=duration)

    @classmethod
    def from_date(cls, date_value: datetime) -> OsDmTimerDefinition:
        return cls(timer_type="date", time_date=date_value)

    @classmethod
    def from_osdm(cls, timer_def: TimerEventDefinition) -> OsDmTimerDefinition:
        """Create from OSDM TimerEventDefinition object."""
        time_date = getattr(timer_def, "time_date", None)
        time_duration = getattr(timer_def, "time_duration", None)
        time_cycle = getattr(timer_def, "time_cycle", None)
        if time_date:
            return cls(timer_type="date", time_date=time_date, time_duration=time_duration, time_cycle=time_cycle)
        if time_cycle:
            return cls(timer_type="cycle", time_cycle=time_cycle, time_duration=time_duration)
        return cls(timer_type="duration", time_duration=time_duration)

    def calculate_deadline(self, reference_time: datetime | None = None) -> datetime:
        ref = reference_time or utc_now()
        if self.timer_type == "duration":
            delta = parse_duration(self.time_duration) if self.time_duration else timedelta()
            return ref + delta
        if self.timer_type == "date":
            return self.time_date or ref
        if self.timer_type == "cycle":
            return self._calculate_cycle_deadline(ref)
        return ref + timedelta(hours=1)

    def _calculate_cycle_deadline(self, ref: datetime) -> datetime:
        """Calculate next cycle deadline from ISO 8601 repeating interval."""
        if not self.time_cycle:
            return ref + timedelta(hours=1)
        try:
            delta = parse_duration(self.time_cycle)
            return ref + delta
        except Exception:
            logger.warning("Failed to parse timer cycle: %s, defaulting to 1h", self.time_cycle)
            return ref + timedelta(hours=1)


class TimerManager:
    """Manages timer jobs that fire callbacks when deadlines are reached."""

    def __init__(self) -> None:
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._handles: dict[str, TimerHandle] = {}

    def schedule(self, name: str, delay: str | int | float, callback: Callable[[], None]) -> str:
        timer_id = f"timer-{uuid4().hex}"
        delay_delta = parse_duration(delay)
        deadline = utc_now() + delay_delta

        async def _runner() -> None:
            try:
                await asyncio.sleep(delay_delta.total_seconds())
                callback()
            except asyncio.CancelledError:
                logger.debug("Timer cancelled: %s", timer_id)
            except Exception as exc:
                logger.error("Timer callback failed: %s — %s", timer_id, exc)
            finally:
                self._tasks.pop(timer_id, None)
                self._handles.pop(timer_id, None)

        task = asyncio.create_task(_runner())
        self._tasks[timer_id] = task
        self._handles[timer_id] = TimerHandle(
            timer_id=timer_id, name=name, callback=callback,
            deadline=deadline, state="pending",
        )
        return timer_id

    def schedule_from_osdm(
        self,
        timer_def: TimerEventDefinition,
        callback: Callable[[], None],
        reference_time: datetime | None = None,
    ) -> str:
        """Schedule a timer job from an OSDM TimerEventDefinition."""
        osdm_timer = OsDmTimerDefinition.from_osdm(timer_def)
        deadline = osdm_timer.calculate_deadline(reference_time)
        timer_id = f"timer-{uuid4().hex}"
        delay_delta = max(timedelta(), deadline - (reference_time or utc_now()))

        async def _runner() -> None:
            try:
                await asyncio.sleep(delay_delta.total_seconds())
                callback()
            except asyncio.CancelledError:
                logger.debug("Timer cancelled: %s", timer_id)
            except Exception as exc:
                logger.error("Timer callback failed: %s — %s", timer_id, exc)
            finally:
                self._tasks.pop(timer_id, None)
                self._handles.pop(timer_id, None)

        task = asyncio.create_task(_runner())
        self._tasks[timer_id] = task
        self._handles[timer_id] = TimerHandle(
            timer_id=timer_id,
            name=getattr(timer_def, "id", timer_id),
            callback=callback,
            deadline=deadline,
            state="pending",
            osdm_timer_definition=osdm_timer,
        )
        return timer_id

    def cancel(self, timer_id: str) -> bool:
        task = self._tasks.pop(timer_id, None)
        self._handles.pop(timer_id, None)
        if task is None:
            return False
        task.cancel()
        return True

    def get_handle(self, timer_id: str) -> TimerHandle | None:
        return self._handles.get(timer_id)

    def get_pending_timers(self) -> list[TimerHandle]:
        return [h for h in self._handles.values() if h.state == "pending"]

    async def shutdown(self) -> None:
        for task in list(self._tasks.values()):
            task.cancel()
        tasks = list(self._tasks.values())
        self._tasks.clear()
        self._handles.clear()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
