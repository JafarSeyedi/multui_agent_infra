from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, asdict, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from .reasoning_event import ReasoningEvent


class ReasoningLevel(str, Enum):
    """
    سطح رویداد استدلالی (برای فیلتر و آنالیز).
    """
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ReasoningPhase(str, Enum):
    """
    فازهای اصلی چرخه ریسرچ برای طبقه‌بندی ترِیس:
    """
    QUERY_UNDERSTANDING = "query_understanding"
    RETRIEVAL = "retrieval"
    GRAPH_BUILDING = "graph_building"
    GRAPH_REASONING = "graph_reasoning"
    PLANNING = "planning"
    SYNTHESIS = "synthesis"
    EVALUATION = "evaluation"
    FEEDBACK = "feedback"
    OTHER = "other"


# @dataclass
# class ReasoningEvent:
#     """
#     یک رویداد واحد در ترِیس استدلال.
#     """
#     id: str
#     timestamp: float
#     session_id: str
#     group: str
#     step: int
#     phase: str
#     event_type: str
#     level: str
#     message: str
#     meta: Dict[str, Any] = field(default_factory=dict)

#     def to_dict(self) -> Dict[str, Any]:
#         d = asdict(self)
#         # تضمین JSON-safe بودن meta
#         if not isinstance(d["meta"], dict):
#             d["meta"] = {"value": str(d["meta"])}
#         return d


class ReasoningMemory:
    """
    ذخیره‌ساز حرفه‌ای ترِیس‌های استدلالی برای کل چرخه Research.

    ویژگی‌ها:
    - پشتیبانی multi-session (session_id)
    - گروه‌بندی منطقی (group)
    - فازهای استاندارد (ReasoningPhase)
    - سطح لاگ (ReasoningLevel)
    - thread-safe
    - API سریالی برای استفاده در Evaluation / Observability
    """

    def __init__(self, max_events: int = 5000) -> None:
        self._lock = threading.RLock()
        self._max_events = max_events

        self._events: List[ReasoningEvent] = []

        self._current_session_id: Optional[str] = None
        self._current_group: Optional[str] = None
        self._step_counter: int = 0

    # ---------- Session / Group Management ----------

    def start_session(self, session_id: Optional[str] = None) -> str:
        """
        شروع یک سشن جدید استدلالی. در صورت عدم ارسال، session_id تولید می‌شود.
        """
        with self._lock:
            self._current_session_id = session_id or str(uuid.uuid4())
            self._current_group = "default"
            self._step_counter = 0

            self._log_internal(
                phase=ReasoningPhase.OTHER,
                event_type="session_start",
                level=ReasoningLevel.INFO,
                message=f"Started reasoning session: {self._current_session_id}",
                meta={},
            )

            return self._current_session_id

    def end_session(self) -> None:
        """
        پایان سشن جاری.
        """
        with self._lock:
            if self._current_session_id is None:
                return

            self._log_internal(
                phase=ReasoningPhase.OTHER,
                event_type="session_end",
                level=ReasoningLevel.INFO,
                message=f"Ended reasoning session: {self._current_session_id}",
                meta={},
            )
            self._current_session_id = None
            self._current_group = None
            self._step_counter = 0

    def start_group(self, group_name: str) -> None:
        """
        شروع یک گروه استدلالی (مثلاً 'research_session', 'retrieval_round_1' و ...).
        """
        with self._lock:
            if self._current_session_id is None:
                # اگر سشن شروع نشده باشد، خودکار یک سشن بساز
                self.start_session()

            self._current_group = group_name
            self._step_counter = 0

            self._log_internal(
                phase=ReasoningPhase.OTHER,
                event_type="group_start",
                level=ReasoningLevel.INFO,
                message=f"Started reasoning group: {group_name}",
                meta={},
            )

    def end_group(self) -> None:
        """
        پایان گروه جاری.
        """
        with self._lock:
            if self._current_group is None:
                return

            self._log_internal(
                phase=ReasoningPhase.OTHER,
                event_type="group_end",
                level=ReasoningLevel.INFO,
                message=f"Ended reasoning group: {self._current_group}",
                meta={},
            )
            self._current_group = None
            self._step_counter = 0

    # ---------- Logging API ----------

    def log(
        self,
        event_type: str,
        message: str,
        meta: Optional[Dict[str, Any]] = None,
        *,
        phase: Union[ReasoningPhase, str] = ReasoningPhase.OTHER,
        level: Union[ReasoningLevel, str] = ReasoningLevel.INFO,
    ) -> None:
        """
        API عمومی برای ثبت رویداد استدلالی.
        برای سازگاری با کد فعلی، پارامترهای اجباری فقط event_type و message هستند.
        """
        if isinstance(phase, ReasoningPhase):
            phase = phase.value
        if isinstance(level, ReasoningLevel):
            level = level.value

        self._log_internal(
            phase=phase,
            event_type=event_type,
            level=level,
            message=message,
            meta=meta or {},
        )

    def _log_internal(
        self,
        phase: str,
        event_type: str,
        level: str,
        message: str,
        meta: Dict[str, Any],
    ) -> None:
        with self._lock:
            if self._current_session_id is None:
                # در صورت نبودن سشن، یک سشن implicit شروع کن
                self._current_session_id = str(uuid.uuid4())
                self._current_group = "implicit"
                self._step_counter = 0

            group = self._current_group or "default"

            event = ReasoningEvent(
                id=str(uuid.uuid4()),
                timestamp=time.time(),
                session_id=self._current_session_id,
                group=group,
                step=self._step_counter,
                phase=phase,
                event_type=event_type,
                level=level,
                message=message,
                meta=meta,
            )

            # مدیریت ظرفیت
            if len(self._events) >= self._max_events:
                # استراتژی ساده: قدیمی‌ترین‌ها را حذف کن
                overflow = len(self._events) + 1 - self._max_events
                if overflow > 0:
                    self._events = self._events[overflow:]

            self._events.append(event)
            self._step_counter += 1

    # ---------- Query & Serialization ----------

    def get_traces(
        self,
        *,
        session_id: Optional[str] = None,
        group: Optional[str] = None,
        phases: Optional[List[str]] = None,
        levels: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        دریافت ترِیس‌ها به صورت JSON-serializable dict.

        اگر session_id/group مشخص نشود، کل ایونت‌ها برگردانده می‌شود.
        """
        with self._lock:
            result: List[ReasoningEvent] = []

            for e in self._events:
                if session_id is not None and e.session_id != session_id:
                    continue
                if group is not None and e.group != group:
                    continue
                if phases is not None and e.phase not in phases:
                    continue
                if levels is not None and e.level not in levels:
                    continue
                result.append(e)

            return [ev.to_dict() for ev in result]

    def get_current_session_traces(self) -> List[Dict[str, Any]]:
        """
        شورتکات: ترِیس‌های سشن جاری.
        """
        with self._lock:
            if self._current_session_id is None:
                return []
            return self.get_traces(session_id=self._current_session_id)

    def clear(self) -> None:
        """
        پاک کردن کل ترِیس‌ها.
        """
        with self._lock:
            self._events.clear()
            self._current_session_id = None
            self._current_group = None
            self._step_counter = 0

    # ---------- Export helpers ----------

    def export_for_evaluation(self) -> List[Dict[str, Any]]:
        """
        خروجی استاندارد برای EvaluationController:
        کل ترِیس‌ها با ساختار ثابت.
        """
        return self.get_traces()

    def export_for_observability(self) -> Dict[str, Any]:
        """
        خروجی مناسب برای سیستم Observability (خلاصه + ترِیس خام).
        """
        with self._lock:
            traces = [e.to_dict() for e in self._events]
            return {
                "total_events": len(traces),
                "sessions": list({e["session_id"] for e in traces}),
                "groups": list({e["group"] for e in traces}),
                "phases": list({e["phase"] for e in traces}),
                "levels": list({e["level"] for e in traces}),
                "events": traces,
            }
