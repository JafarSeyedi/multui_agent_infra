from __future__ import annotations

import threading
import time
import uuid
from enum import Enum
from typing import Any

from .reasoning_event import ReasoningEvent


class ReasoningLevel(str, Enum):
    """
    Reasoning event level (for filter and analysis).
    """
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ReasoningPhase(str, Enum):
    """
    Main phases of the research cycle for trace classification:
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
#     A single event in the reasoning trace.
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
#         # Guarantee that meta is JSON-safe
#         if not isinstance(d["meta"], dict):
#             d["meta"] = {"value": str(d["meta"])}
#         return d


class ReasoningMemory:
    """
    Professional trace storage for the entire Research cycle.

    Features:
    - Multi-session support (session_id)
    - Logical grouping (group)
    - Standard phases (ReasoningPhase)
    - Log level (ReasoningLevel)
    - thread-safe
    - Serialization API for use in Evaluation / Observability
    """

    def __init__(self, max_events: int = 5000) -> None:
        self._lock = threading.RLock()
        self._max_events = max_events

        self._events: list[ReasoningEvent] = []

        self._current_session_id: str | None = None
        self._current_group: str | None = None
        self._step_counter: int = 0

    # ---------- Session / Group Management ----------

    def start_session(self, session_id: str | None = None) -> str:
        """
        Start a new reasoning session. If not provided, a session_id is generated.
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
        End the current session.
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
        Start a reasoning group (e.g., 'research_session', 'retrieval_round_1', etc.).
        """
        with self._lock:
            if self._current_session_id is None:
                # If no session has started, auto-create one
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
        End the current group.
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
        meta: dict[str, Any] | None = None,
        *,
        phase: ReasoningPhase | str = ReasoningPhase.OTHER,
        level: ReasoningLevel | str = ReasoningLevel.INFO,
    ) -> None:
        """
        Public API for recording reasoning events.
        For compatibility with current code, the only required parameters are event_type and message.
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
        meta: dict[str, Any],
    ) -> None:
        with self._lock:
            if self._current_session_id is None:
                # If no session exists, start an implicit session
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

            # Capacity management
            if len(self._events) >= self._max_events:
                # Simple strategy: remove oldest ones
                overflow = len(self._events) + 1 - self._max_events
                if overflow > 0:
                    self._events = self._events[overflow:]

            self._events.append(event)
            self._step_counter += 1

    # ---------- Query & Serialization ----------

    def get_traces(
        self,
        *,
        session_id: str | None = None,
        group: str | None = None,
        phases: list[str] | None = None,
        levels: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get traces as JSON-serializable dict.

        If session_id/group is not specified, all events are returned.
        """
        with self._lock:
            result: list[ReasoningEvent] = []

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

    def get_current_session_traces(self) -> list[dict[str, Any]]:
        """
        Shortcut: current session traces.
        """
        with self._lock:
            if self._current_session_id is None:
                return []
            return self.get_traces(session_id=self._current_session_id)

    def clear(self) -> None:
        """
        Clear all traces.
        """
        with self._lock:
            self._events.clear()
            self._current_session_id = None
            self._current_group = None
            self._step_counter = 0

    # ---------- Export helpers ----------

    def export_for_evaluation(self) -> list[dict[str, Any]]:
        """
        Standard output for EvaluationController:
        All traces with fixed structure.
        """
        return self.get_traces()

    def export_for_observability(self) -> dict[str, Any]:
        """
        Output suitable for Observability system (summary + raw traces).
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
