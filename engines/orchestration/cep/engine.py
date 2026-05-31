"""CEP engine with windowing, correlation, and persistence.

Coordinates pattern execution and durable streaming/runtime state at CEP level.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from ..core.context import ContextManager, ContextScope
from ..core.engine import OrchestrationEngine, ProcessDefinition
from ..core.instance import InstanceState, ProcessInstance
from ..core.event_bus import Event, EventType
from ..runtime.state_manager import StateManager
from .stream_processor import StreamProcessor
from .pattern_matcher import PatternMatcher
from .window_manager import WindowManager
from .aggregator import Aggregator
from .rule_evaluator import RuleEvaluator
from .event_store import CEPEventStore


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CEPExecutionError(RuntimeError):
    """Raised when CEP execution fails."""


class CEPEngine:
    """Orchestrates complex event processing with durable state."""

    def __init__(
        self,
        orchestration_engine: OrchestrationEngine,
        *,
        state_manager: StateManager | None = None,
    ) -> None:
        self.orchestration_engine = orchestration_engine
        self.context_manager = ContextManager()
        self.state_manager = state_manager or orchestration_engine.state_manager
        self.stream_processor = StreamProcessor()
        self.pattern_matcher = PatternMatcher()
        self.window_manager = WindowManager()
        self.aggregator = Aggregator()
        self.rule_evaluator = RuleEvaluator()
        self.event_store = CEPEventStore()

    async def execute_instance(self, instance: ProcessInstance, definition: ProcessDefinition) -> None:
        context_id = instance.id
        definition_payload: dict[str, Any] = {}

        if isinstance(definition.definition_xml, dict):
            definition_payload = definition.definition_xml

        definition_payload["_engine_type"] = "cep"
        definition_payload["_definition_key"] = definition.key

        self.context_manager.create_context(ContextScope.PROCESS, context_id)
        logger.info("CEP engine executing instance %s", instance.id)

        await self.state_manager.set_persisted(
            context_id,
            "running",
            data={"definition_key": definition.key, "definition_id": definition.id},
        )

        try:
            events = definition_payload.get("events", [])
            rules = definition_payload.get("rules", [])
            patterns = definition_payload.get("patterns", [])
            window_config = definition_payload.get("window", {})

            if window_config:
                self.window_manager.configure(instance.id, window_config)

            for event_data in events:
                processed = await self.stream_processor.process(event_data, instance)
                self.event_store.store(instance.id, processed)

            for pattern in patterns:
                match_result = self.pattern_matcher.evaluate(pattern, instance.get_all_variables(), instance.id)
                if match_result.get("matched"):
                    instance.set_variable(f"pattern.{pattern.get('id', 'unknown')}", match_result)
                    if self.orchestration_engine is not None:
                        self.orchestration_engine.event_bus.publish(
                            Event(
                                type=EventType.ACTIVITY_COMPLETED,
                                data={
                                    "instance_id": instance.id,
                                    "pattern_id": pattern.get("id"),
                                    "match": match_result,
                                },
                            )
                        )

            for rule in rules:
                rule_result = await self.rule_evaluator.evaluate(rule, instance.get_all_variables(), instance)
                if rule_result is not None:
                    rule_var = rule.get("outputVariable", f"rule.{rule.get('id', 'unknown')}")
                    instance.set_variable(rule_var, rule_result)

            aggregation_config = definition_payload.get("aggregations", [])
            for agg in aggregation_config:
                agg_result = self.aggregator.aggregate(agg, instance.get_all_variables())
                if agg_result is not None:
                    agg_var = agg.get("outputVariable", f"agg.{agg.get('id', 'unknown')}")
                    instance.set_variable(agg_var, agg_result)

        except Exception as exc:
            await self.orchestration_engine.update_instance_state(
                instance.id, InstanceState.FAILED, reason=str(exc)
            )
            await self.state_manager.set_persisted(
                context_id,
                "failed",
                data={"definition_key": definition.key, "definition_id": definition.id, "error": str(exc)},
            )
            raise

        await self.orchestration_engine.update_instance_state(instance.id, InstanceState.COMPLETED)
        await self.state_manager.set_persisted(
            context_id,
            "completed",
            data={"definition_key": definition.key, "definition_id": definition.id},
        )
        logger.info("CEP instance completed: %s", instance.id)
