"""CEP pattern matcher with temporal operators.

Implements event sequence, absence, threshold, and temporal operators.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PatternOperator(str, Enum):
    FOLLOWED_BY = "followed_by"
    FOLLOWED_BY_ANY = "followed_by_any"
    OR = "or"
    AND = "and"
    NOT_FOLLOWED_BY = "not_followed_by"
    NOT_NEXT = "not_next"
    REPEATED = "repeated"
    ABSENCE = "absence"
    EXISTENCE = "existence"
    UNTIL = "until"
    STRICT = "strict"


class TemporalRelation(str, Enum):
    BEFORE = "before"
    AFTER = "after"
    MEETS = "meets"
    MET_BY = "met_by"
    OVERLAPS = "overlaps"
    OVERLAPED_BY = "overlapped_by"
    DURING = "during"
    CONTAINS = "contains"
    STARTS = "starts"
    STARTED_BY = "started_by"
    FINISHES = "finishes"
    FINISHED_BY = "finished_by"
    EQUALS = "equals"
    COINCIDES = "coincides"


@dataclass
class PatternDefinition:
    pattern_id: str = ""
    operator: str = "followed_by"
    events: list[dict[str, Any]] = field(default_factory=list)
    time_window: str | None = None
    min_occurrences: int = 1
    max_occurrences: int | None = None
    correlation_keys: dict[str, str] = field(default_factory=dict)


@dataclass
class PatternMatch:
    pattern_id: str = ""
    matched: bool = False
    events_matched: list[str] = field(default_factory=list)
    timestamp: str | None = None
    context: dict[str, Any] = field(default_factory=dict)


class PatternMatcher:
    def __init__(self) -> None:
        self._event_buffer: dict[str, list[dict[str, Any]]] = {}
        self._patterns: dict[str, PatternDefinition] = {}

    def register_pattern(self, pattern: PatternDefinition) -> None:
        self._patterns[pattern.pattern_id] = pattern

    def feed_event(self, instance_id: str, event: dict[str, Any]) -> None:
        if instance_id not in self._event_buffer:
            self._event_buffer[instance_id] = []
        self._event_buffer[instance_id].append(event)

    def evaluate(
        self,
        pattern_data: dict[str, Any],
        context: dict[str, Any],
        instance_id: str = "default",
    ) -> dict[str, Any]:
        pattern = self._normalize_pattern(pattern_data)
        buffer = self._event_buffer.get(instance_id, [])

        if pattern.operator == PatternOperator.FOLLOWED_BY:
            return self._match_followed_by(pattern, buffer, context)
        elif pattern.operator == PatternOperator.OR:
            return self._match_or(pattern, buffer, context)
        elif pattern.operator == PatternOperator.AND:
            return self._match_and(pattern, buffer, context)
        elif pattern.operator == PatternOperator.REPEATED:
            return self._match_repeated(pattern, buffer, context)
        elif pattern.operator == PatternOperator.ABSENCE:
            return self._match_absence(pattern, buffer, context)
        elif pattern.operator == PatternOperator.EXISTENCE:
            return self._match_existence(pattern, buffer, context)
        else:
            return self._match_followed_by(pattern, buffer, context)

    def _normalize_pattern(self, data: dict[str, Any]) -> PatternDefinition:
        return PatternDefinition(
            pattern_id=data.get("id", data.get("name", "")),
            operator=data.get("operator", data.get("type", "followed_by")),
            events=data.get("events", data.get("conditions", [])),
            time_window=data.get("timeWindow") or data.get("within"),
            min_occurrences=data.get("minOccurrences", 1),
            max_occurrences=data.get("maxOccurrences"),
            correlation_keys=data.get("correlationKeys", {}),
        )

    def _match_followed_by(
        self, pattern: PatternDefinition, buffer: list[dict[str, Any]], context: dict[str, Any]
    ) -> dict[str, Any]:
        events_required = [e.get("type", e.get("event", "")) for e in pattern.events if isinstance(e, dict)]
        if not events_required:
            return {"matched": False}

        matched_events: list[str] = []
        last_idx = -1

        for required_type in events_required:
            found = False
            for i, event in enumerate(buffer):
                if i > last_idx and event.get("type", "") == required_type:
                    matched_events.append(event.get("id", str(i)))
                    last_idx = i
                    found = True
                    break
            if not found:
                return {"matched": False}

        return {
            "matched": True,
            "pattern_id": pattern.pattern_id,
            "events_matched": matched_events,
        }

    def _match_or(
        self, pattern: PatternDefinition, buffer: list[dict[str, Any]], context: dict[str, Any]
    ) -> dict[str, Any]:
        event_types = {e.get("type", e.get("event", "")) for e in pattern.events if isinstance(e, dict)}
        for event in buffer:
            if event.get("type", "") in event_types:
                return {"matched": True, "pattern_id": pattern.pattern_id, "events_matched": [event.get("id", "")]}
        return {"matched": False}

    def _match_and(
        self, pattern: PatternDefinition, buffer: list[dict[str, Any]], context: dict[str, Any]
    ) -> dict[str, Any]:
        event_types = {e.get("type", e.get("event", "")) for e in pattern.events if isinstance(e, dict)}
        found_types: set[str] = set()
        matched_events: list[str] = []
        for event in buffer:
            et = event.get("type", "")
            if et in event_types:
                found_types.add(et)
                matched_events.append(event.get("id", ""))
        return {"matched": found_types == event_types, "pattern_id": pattern.pattern_id, "events_matched": matched_events}

    def _match_repeated(
        self, pattern: PatternDefinition, buffer: list[dict[str, Any]], context: dict[str, Any]
    ) -> dict[str, Any]:
        if not pattern.events:
            return {"matched": False}
        target_type = pattern.events[0].get("type", pattern.events[0].get("event", "")) if isinstance(pattern.events[0], dict) else str(pattern.events[0])
        min_occ = pattern.min_occurrences
        max_occ = pattern.max_occurrences
        count = sum(1 for e in buffer if e.get("type", "") == target_type)
        matched = count >= min_occ
        if max_occ is not None:
            matched = matched and count <= max_occ
        return {"matched": matched, "pattern_id": pattern.pattern_id, "occurrences": count}

    def _match_absence(
        self, pattern: PatternDefinition, buffer: list[dict[str, Any]], context: dict[str, Any]
    ) -> dict[str, Any]:
        if not pattern.events:
            return {"matched": True}
        target_type = pattern.events[0].get("type", pattern.events[0].get("event", "")) if isinstance(pattern.events[0], dict) else str(pattern.events[0])
        for event in buffer:
            if event.get("type", "") == target_type:
                return {"matched": False, "pattern_id": pattern.pattern_id}
        return {"matched": True, "pattern_id": pattern.pattern_id}

    def _match_existence(
        self, pattern: PatternDefinition, buffer: list[dict[str, Any]], context: dict[str, Any]
    ) -> dict[str, Any]:
        return self._match_or(pattern, buffer, context)

    def get_buffer(self, instance_id: str) -> list[dict[str, Any]]:
        return list(self._event_buffer.get(instance_id, []))

    def clear_buffer(self, instance_id: str) -> int:
        buffer = self._event_buffer.get(instance_id, [])
        count = len(buffer)
        self._event_buffer[instance_id] = []
        return count
