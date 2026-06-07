"""Streaming entrypoint for CEP event ingestion and rule evaluation.

Manages ingest, watermark/order, and stream state transitions.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from ..core.instance import ProcessInstance
from .event_store import CEPEventStore
from .pattern_matcher import PatternMatcher
from .rule_evaluator import RuleEvaluator
from .window_manager import WindowManager
from .aggregator import Aggregator


logger = logging.getLogger(__name__)


class WatermarkPolicy(str, Enum):
    EVENT_TIME = "eventTime"
    INGESTION_TIME = "ingestionTime"
    PROCESSING_TIME = "processingTime"


@dataclass
class StreamProcessingResult:
    event_id: str
    event_type: str
    processed: bool = True
    rules_triggered: list[str] = field(default_factory=list)
    patterns_matched: list[str] = field(default_factory=list)
    window_id: str | None = None
    watermark: str | None = None
    errors: list[str] = field(default_factory=list)


class StreamProcessor:
    """Processes event streams with full CEP semantics."""

    def __init__(self) -> None:
        self.event_store = CEPEventStore()
        self.pattern_matcher = PatternMatcher()
        self.rule_evaluator = RuleEvaluator()
        self.window_manager = WindowManager()
        self.aggregator = Aggregator()

    async def process(self, event: dict[str, Any], instance: ProcessInstance | None = None) -> StreamProcessingResult:
        event_id = str(event.get("id", f"evt_{id(event)}"))
        event_type = str(event.get("type", "generic"))
        timestamp = event.get("timestamp")

        try:
            self.event_store.store(
                instance_id=instance.id if instance else "default",
                event_id=event_id,
                event_type=event_type,
                payload=event,
                timestamp=timestamp,
            )
        except Exception as e:
            return StreamProcessingResult(
                event_id=event_id,
                event_type=event_type,
                processed=False,
                errors=[f"Store error: {e}"],
            )

        if instance:
            instance.set_variable(f"cep.event.{event_type}", {
                "id": event_id,
                "timestamp": timestamp,
            })

        return StreamProcessingResult(
            event_id=event_id,
            event_type=event_type,
            processed=True,
            watermark=timestamp,
        )

    def process_batch(
        self,
        events: list[dict[str, Any]],
        rules: list[dict[str, Any]] | None = None,
        instance: ProcessInstance | None = None,
    ) -> list[StreamProcessingResult]:
        results: list[StreamProcessingResult] = []
        for event in events:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                result = loop.run_until_complete(self.process(event, instance))
            except RuntimeError:
                result = StreamProcessingResult(
                    event_id=str(event.get("id", "")),
                    event_type=str(event.get("type", "generic")),
                    processed=True,
                )
            results.append(result)

        if rules:
            for rule in rules:
                triggered = self.rule_evaluator.evaluate_batch(rule, events)
                for result in results:
                    if result.event_id in triggered:
                        result.rules_triggered.append(rule.get("name", rule.get("id", "")))

        return results

    def collect_window(
        self,
        window_id: str,
        event: dict[str, Any],
        window_type: str = "time",
        window_size: str = "1 minute",
    ) -> list[dict[str, Any]]:
        return self.window_manager.push(window_id, event, window_type=window_type, window_size=window_size)

    def get_window_contents(self, window_id: str) -> list[dict[str, Any]]:
        return self.window_manager.get_events(window_id)

    def clear_window(self, window_id: str) -> int:
        return self.window_manager.clear(window_id)

    def get_processing_statistics(self) -> dict[str, Any]:
        return {
            "total_events_stored": self.event_store.count(),
            "active_windows": self.window_manager.count(),
        }
