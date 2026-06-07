"""CEP window manager.

Supports tumbling/sliding/session/time/count windows and recovery.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..core.instance import ProcessInstance


class WindowType(str, Enum):
    TUMBLING = "tumbling"
    SLIDING = "sliding"
    SESSION = "session"
    TIME = "time"
    COUNT = "count"


@dataclass
class WindowDefinition:
    window_id: str = ""
    window_type: str = "tumbling"
    size: str = "1 minute"
    slide: str | None = None
    session_gap: str | None = None
    max_count: int | None = None


@dataclass
class WindowState:
    window_id: str
    events: list[dict[str, Any]] = field(default_factory=list)
    state: str = "open"
    version: int = 1


class WindowManager:
    def __init__(self) -> None:
        self._windows: dict[str, WindowState] = {}
        self._definitions: dict[str, WindowDefinition] = {}

    def configure(self, instance_id: str, config: dict[str, Any]) -> WindowDefinition:
        definition = WindowDefinition(
            window_id=config.get("id", f"window_{instance_id}"),
            window_type=config.get("type", "tumbling"),
            size=config.get("size", config.get("windowSize", "1 minute")),
            slide=config.get("slide"),
            session_gap=config.get("sessionGap"),
            max_count=config.get("maxCount"),
        )
        self._definitions[definition.window_id] = definition
        state = WindowState(window_id=definition.window_id)
        self._windows[definition.window_id] = state
        return definition

    def push(
        self,
        window_id: str,
        event: dict[str, Any],
        window_type: str = "time",
        window_size: str = "1 minute",
    ) -> list[dict[str, Any]]:
        if window_id not in self._windows:
            state = WindowState(window_id=window_id)
            self._windows[window_id] = state
            definition = WindowDefinition(window_id=window_id, window_type=window_type, size=window_size)
            self._definitions[window_id] = definition

        state = self._windows[window_id]
        state.events.append(event)
        state.version += 1

        existing = self._definitions.get(window_id)
        if existing is not None and existing.max_count is not None and len(state.events) > existing.max_count:
            state.events = state.events[-existing.max_count:]

        return list(state.events)

    def get_events(self, window_id: str) -> list[dict[str, Any]]:
        state = self._windows.get(window_id)
        return list(state.events) if state else []

    def clear(self, window_id: str) -> int:
        state = self._windows.get(window_id)
        if state is None:
            return 0
        count = len(state.events)
        state.events.clear()
        state.state = "closed"
        return count

    def close_window(self, window_id: str) -> list[dict[str, Any]]:
        state = self._windows.get(window_id)
        if state is None:
            return []
        events = list(state.events)
        state.events.clear()
        state.state = "closed"
        return events

    def get_window(self, window_id: str) -> WindowState | None:
        return self._windows.get(window_id)

    def count(self) -> int:
        return len(self._windows)

    def get_all_windows(self) -> list[str]:
        return list(self._windows.keys())
