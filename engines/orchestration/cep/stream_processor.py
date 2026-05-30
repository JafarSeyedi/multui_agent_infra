"""Streaming entrypoint for CEP event ingestion and rule evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Any

from .event_store import EventStore
from .pattern_matcher import Pattern, PatternMatcher
from .rule_evaluator import Rule, RuleEvaluator
from .window_manager import TimeWindow, WindowManager


@dataclass(frozen=True)
class StreamProcessor:
    event_store: EventStore = EventStore()
    pattern_matcher: PatternMatcher = PatternMatcher()
    rule_evaluator: RuleEvaluator = RuleEvaluator()
    window_manager: WindowManager = WindowManager()

    def process(self, event: dict, *, rules: list[Rule], callback: Callable[[Rule, dict], None] | None = None) -> list[str]:
        event_id = str(event.get("id", "evt"))
        event_type = str(event.get("type", "generic"))
        self.event_store.append(event_id=event_id, event_type=event_type, payload=event)
        triggered = []
        for rule in rules:
            if self.rule_evaluator.evaluate(rule, event):
                if callback:
                    callback(rule, event)
                triggered.append(rule.name)
        return triggered

    def collect_window(self, window_id: str, event: dict, window: TimeWindow) -> list[dict]:
        return self.window_manager.push(window_id, event, window=window)
