"""State machine history management.

Supports shallow/deep history persistence and restoration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class HistoryKind(str, Enum):
    SHALLOW = "shallowHistory"
    DEEP = "deepHistory"


from enum import Enum


@dataclass
class HistoryEntry:
    instance_id: str
    source_state: str
    target_state: str
    trigger: str | None = None
    timestamp: str = ""
    region_id: str | None = None


@dataclass
class StateMachineHistory:
    def __init__(self) -> None:
        self._history: dict[str, list[HistoryEntry]] = {}
        self._shallow_history: dict[str, dict[str, str]] = {}
        self._deep_history: dict[str, dict[str, list[str]]] = {}

    def push(
        self,
        instance_id: str,
        source_state: str,
        target_state: str,
        trigger: str | None = None,
    ) -> None:
        if instance_id not in self._history:
            self._history[instance_id] = []
        from datetime import datetime
        entry = HistoryEntry(
            instance_id=instance_id,
            source_state=source_state,
            target_state=target_state,
            trigger=trigger,
            timestamp=datetime.utcnow().isoformat(),
        )
        self._history[instance_id].append(entry)

    def get_history(self, instance_id: str) -> list[dict[str, Any]]:
        entries = self._history.get(instance_id, [])
        return [
            {
                "source": e.source_state,
                "target": e.target_state,
                "trigger": e.trigger,
                "timestamp": e.timestamp,
            }
            for e in entries
        ]

    def record_shallow_history(self, instance_id: str, region_id: str, state_id: str) -> None:
        if instance_id not in self._shallow_history:
            self._shallow_history[instance_id] = {}
        self._shallow_history[instance_id][region_id] = state_id

    def get_shallow_history(self, instance_id: str, region_id: str) -> str | None:
        return self._shallow_history.get(instance_id, {}).get(region_id)

    def record_deep_history(self, instance_id: str, region_id: str, states: list[str]) -> None:
        if instance_id not in self._deep_history:
            self._deep_history[instance_id] = {}
        self._deep_history[instance_id][region_id] = states

    def get_deep_history(self, instance_id: str, region_id: str) -> list[str] | None:
        return self._deep_history.get(instance_id, {}).get(region_id)

    def get_last_transition(self, instance_id: str) -> HistoryEntry | None:
        entries = self._history.get(instance_id, [])
        return entries[-1] if entries else None

    def clear(self, instance_id: str) -> None:
        self._history.pop(instance_id, None)
        self._shallow_history.pop(instance_id, None)
        self._deep_history.pop(instance_id, None)

    def get_transition_count(self, instance_id: str) -> int:
        return len(self._history.get(instance_id, []))
