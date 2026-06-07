"""Loop and multi-instance handler for BPMN activities.

Supports standard loops, multi-instance (sequential/parallel),
completion conditions, cardinality, and collections.

Uses OSDM-typed objects for all loop characteristics:
  - LoopCharacteristics (base)
  - StandardLoopCharacteristics
  - MultiInstanceLoopCharacteristics
  - Activity.loop_characteristics

Backward-compatible dict-based construction is preserved.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from ..core.engine import OrchestrationEngine

from ...document.models.osdm_models import (
    Activity,
    LoopCharacteristics,
    StandardLoopCharacteristics,
    MultiInstanceLoopCharacteristics,
    MultiInstanceBehavior,
    LoopType,
    FormalExpression,
)


# ═══════════════════════════════════════════════════════════════
# FormalExpression helper
# ═══════════════════════════════════════════════════════════════

def _extract_fe_value(expr: FormalExpression | None, default: str | None = None) -> str | None:
    """Extract the string body from a FormalExpression.

    FormalExpression.body holds the textual content of the expression.
    Returns *default* when *expr* is None or its body is None.
    """
    if expr is None:
        return default
    return expr.body if expr.body is not None else default


def _extract_fe_int(expr: FormalExpression | None, default: int = 0) -> int:
    """Extract an integer value from a FormalExpression body.

    Attempts to parse ``expr.body`` as an int. Falls back to *default*
    when parsing fails or *expr* is ``None``.
    """
    raw = _extract_fe_value(expr)
    if raw is None:
        return default
    try:
        return int(raw)
    except (ValueError, TypeError):
        return default


# ═══════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════

@dataclass
class HandlerLoopConfiguration:
    loop_type: str = LoopType.NONE
    repeat_count: int = 0
    test_before: bool = False
    max_iterations: int | None = None
    loop_condition: str | None = None
    is_sequential: bool = False
    cardinality_value: int = 1
    completion_condition: str | None = None
    collection_variable: str | None = None
    element_variable: str | None = None
    element_index: str | None = None
    behavior: str = MultiInstanceBehavior.ALL
    loop_data_input_ref: str | None = None
    loop_data_output_ref: str | None = None

    @staticmethod
    def from_loop_characteristics(
        loop_chars: LoopCharacteristics | None,
    ) -> HandlerLoopConfiguration:
        """Build a HandlerLoopConfiguration from an OSDM ``LoopCharacteristics`` object.

        Returns an identity/no-op configuration when *loop_chars* is ``None``.
        """
        if loop_chars is None:
            return HandlerLoopConfiguration()

        lt = loop_chars.loop_type

        if lt == LoopType.STANDARD and isinstance(loop_chars, StandardLoopCharacteristics):
            slc: StandardLoopCharacteristics = loop_chars
            return HandlerLoopConfiguration(
                loop_type=LoopType.STANDARD,
                test_before=slc.test_before,
                max_iterations=slc.loop_maximum if slc.loop_maximum else 1000,
                loop_condition=_extract_fe_value(slc.loop_condition),
            )

        if lt == LoopType.MULTI_INSTANCE and isinstance(loop_chars, MultiInstanceLoopCharacteristics):
            milc: MultiInstanceLoopCharacteristics = loop_chars
            card = _extract_fe_int(milc.loop_cardinality, 1)
            return HandlerLoopConfiguration(
                loop_type=LoopType.MULTI_INSTANCE,
                is_sequential=milc.is_sequential,
                cardinality_value=card if card > 0 else 1,
                loop_condition=_extract_fe_value(milc.completion_condition),
                behavior=milc.behavior if isinstance(milc.behavior, str) else milc.behavior.value,
                loop_data_input_ref=milc.loop_data_input_ref.id if milc.loop_data_input_ref is not None else None,
                loop_data_output_ref=milc.loop_data_output_ref.id if milc.loop_data_output_ref is not None else None,
            )

        return HandlerLoopConfiguration(loop_type=lt if isinstance(lt, str) else lt.value)

    @staticmethod
    def from_osdm(activity: Activity) -> HandlerLoopConfiguration:
        """Create a ``HandlerLoopConfiguration`` from an OSDM Activity's
        ``loop_characteristics`` field.

        This is the primary entry point for configuring a handler from a
        parsed BPMN activity.  Falls back to a no-op configuration when
        no loop characteristics are present.
        """
        return HandlerLoopConfiguration.from_loop_characteristics(
            activity.loop_characteristics
        )


# ═══════════════════════════════════════════════════════════════
# Iteration / State / Outcome
# ═══════════════════════════════════════════════════════════════

@dataclass
class HandlerLoopIteration:
    index: int
    element: Any = None
    completed: bool = False
    result: Any = None


@dataclass
class HandlerLoopState:
    activity_id: str
    loop_type: str = LoopType.NONE
    current_iteration: int = 0
    total_iterations: int = 0
    iterations: list[HandlerLoopIteration] = field(default_factory=list)
    is_complete: bool = False
    collection_data: list[Any] = field(default_factory=list)
    aggregated_output: dict[str, Any] = field(default_factory=dict)
    failed_iteration: bool = False


@dataclass
class HandlerLoopOutcome:
    activity_id: str
    completed: bool = False
    iteration_results: list[Any] = field(default_factory=list)
    total_iterations: int = 0
    failed_iterations: int = 0
    aggregated_output: dict[str, Any] = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════
# Handler
# ═══════════════════════════════════════════════════════════════

class LoopHandler:
    def __init__(self, orchestration_engine: OrchestrationEngine | None = None) -> None:
        self._engine = orchestration_engine
        self._states: dict[str, HandlerLoopState] = {}
        self._executors: dict[str, Callable] = {}

    # ── public API ──────────────────────────────────────────────

    def execute(
        self,
        config: HandlerLoopConfiguration,
        callback: Callable[[int, Any], Any],
        context: dict[str, Any] | None = None,
    ) -> HandlerLoopOutcome:
        context = context or {}
        loop_type = config.loop_type

        if loop_type == LoopType.NONE:
            result = callback(0, None)
            return HandlerLoopOutcome(
                activity_id="",
                completed=True,
                iteration_results=[result],
                total_iterations=1,
            )
        elif loop_type == LoopType.STANDARD:
            return self._execute_standard(config, callback, context)
        elif loop_type == LoopType.MULTI_INSTANCE:
            return self._execute_multi_instance(config, callback, context)

        result = callback(0, None)
        return HandlerLoopOutcome(
            activity_id="",
            completed=True,
            iteration_results=[result],
            total_iterations=1,
        )

    def _execute_standard(self, config, callback, context):
        max_iter = config.max_iterations or 1000
        results = []
        test_before = config.test_before
        if test_before and config.loop_condition:
            if self._evaluate_condition(config.loop_condition, context):
                results.append(callback(0, None))
                return HandlerLoopOutcome(
                    activity_id="",
                    completed=True,
                    iteration_results=results,
                    total_iterations=1,
                )
        for i in range(max_iter):
            result = callback(i, None)
            results.append(result)
            if config.loop_condition and self._evaluate_condition(config.loop_condition, context):
                break
        return HandlerLoopOutcome(
            activity_id="",
            completed=True,
            iteration_results=results,
            total_iterations=len(results),
        )

    def _execute_multi_instance(self, config, callback, context):
        collection = self._resolve_collection(config, context)
        is_sequential = config.is_sequential
        if not collection:
            return HandlerLoopOutcome(
                activity_id="",
                completed=True,
                iteration_results=[],
                total_iterations=0,
            )
        total = len(collection)
        results = []
        failed = 0
        if is_sequential:
            for i, element in enumerate(collection):
                try:
                    results.append(callback(i, element))
                except Exception:
                    failed += 1
                    if config.behavior == MultiInstanceBehavior.ALL:
                        break
        else:
            for i, element in enumerate(collection):
                try:
                    results.append(callback(i, element))
                except Exception:
                    failed += 1
        return HandlerLoopOutcome(
            activity_id="",
            completed=True,
            iteration_results=results,
            total_iterations=total,
            failed_iterations=failed,
            aggregated_output={
                "completed": len(results),
                "failed": failed,
                "total": total,
            },
        )

    def _resolve_collection(self, config, context):
        if config.loop_data_input_ref:
            data = context.get(config.loop_data_input_ref)
            if isinstance(data, list):
                return data
        if config.collection_variable:
            data = context.get(config.collection_variable)
            if isinstance(data, list):
                return data
        return list(range(max(1, config.cardinality_value)))

    def _evaluate_condition(self, condition, context):
        if condition in {"true", "True", "1"}:
            return True
        if condition in {"false", "False", "0"}:
            return False
        try:
            from ..expression.evaluator import EvaluationContext
            from ..expression.python_evaluator import PythonEvaluator

            return bool(
                PythonEvaluator().evaluate(condition, EvaluationContext(variables=context))
            )
        except Exception:
            return False

    def start_loop(self, activity_id, config, callback, context=None):
        context = context or {}
        total = config.cardinality_value
        if config.collection_variable and config.collection_variable in context:
            collection = context[config.collection_variable]
            if isinstance(collection, list):
                total = len(collection)
        state = HandlerLoopState(
            activity_id=activity_id,
            loop_type=config.loop_type,
            total_iterations=total,
            collection_data=self._resolve_collection(config, context),
        )
        for i in range(total):
            element = state.collection_data[i] if i < len(state.collection_data) else None
            state.iterations.append(HandlerLoopIteration(index=i, element=element))
        self._states[activity_id] = state
        self._executors[activity_id] = callback
        return state

    def execute_next(self, activity_id, context=None):
        state = self._states.get(activity_id)
        if state is None:
            return None
        callback = self._executors.get(activity_id)
        if callback is None:
            return None
        for iteration in state.iterations:
            if not iteration.completed:
                try:
                    iteration.result = callback(iteration.index, iteration.element)
                    iteration.completed = True
                    state.current_iteration = iteration.index + 1
                    return iteration
                except Exception:
                    state.failed_iteration = True
                    iteration.completed = True
                    state.current_iteration = iteration.index + 1
                    return iteration
        state.is_complete = True
        return None

    def is_complete(self, activity_id):
        state = self._states.get(activity_id)
        return state is not None and state.is_complete

    def cancel_remaining(self, activity_id):
        state = self._states.get(activity_id)
        if state is None:
            return 0
        cancelled = sum(1 for it in state.iterations if not it.completed)
        for it in state.iterations:
            it.completed = True
        state.is_complete = True
        return cancelled

    def get_progress(self, activity_id):
        state = self._states.get(activity_id)
        if state is None:
            return None
        completed = sum(1 for it in state.iterations if it.completed)
        return {
            "total": len(state.iterations),
            "completed": completed,
            "remaining": len(state.iterations) - completed,
            "is_complete": state.is_complete,
            "failed": state.failed_iteration,
        }
