"""Event pattern matching utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Pattern:
    name: str
    event_type: str


class PatternMatcher:
    def match(self, history: list[dict[str, Any]], pattern: Pattern) -> bool:
        return any(item.get("type") == pattern.event_type for item in history)
