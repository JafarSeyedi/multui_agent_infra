"""DMN decision executor with decision graph traversal and dependency resolution.

Supports decision tables, literal expressions, invocations, and BKM calls
at DMN 1.3 specification level.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from ...core.instance import ProcessInstance
from ...core.engine import OrchestrationEngine
from .decision_table_evaluator import DecisionTableEvaluator
from .literal_expression_eval import LiteralExpressionEvaluator
from .invocation_handler import InvocationHandler
from .feel_engine import FEELEngine
from .hit_policy_handler import HitPolicyHandler


logger = logging.getLogger(__name__)


@dataclass
class DecisionNode:
    decision_id: str
    name: str | None = None
    decision_table: dict[str, Any] | None = None
    literal_expression: str | None = None
    required_decisions: list[str] = field(default_factory=list)
    required_inputs: list[str] = field(default_factory=list)
    invoked_bkm: str | None = None
    variable_name: str | None = None


@dataclass
class DecisionResult:
    decision_id: str
    result: Any = None
    status: str = "completed"
    errors: list[str] = field(default_factory=list)
    rule_results: list[dict[str, Any]] = field(default_factory=list)
    hit_policy_applied: str | None = None
    evaluation_time_ms: float = 0.0


class DecisionExecutor:
    def __init__(self, orchestration_engine: OrchestrationEngine | None = None) -> None:
        self.orchestration_engine = orchestration_engine
        self.table_evaluator = DecisionTableEvaluator()
        self.literal_evaluator = LiteralExpressionEvaluator()
        self.invocation_handler = InvocationHandler()
        self.feel_engine = FEELEngine()
        self.hit_policy_handler = HitPolicyHandler()
        self._decision_cache: dict[str, DecisionResult] = {}

    async def evaluate(
        self,
        decision: dict[str, Any],
        context: dict[str, Any],
        instance: ProcessInstance | None = None,
    ) -> Any:
        decision_id = decision.get("id", "unknown")
        name = decision.get("name", decision_id)
        variable_name = decision.get("variable", {}).get("name", "decision_result")

        logger.debug("Evaluating DMN decision: %s (%s)", name, decision_id)

        if decision_id in self._decision_cache:
            cached = self._decision_cache[decision_id]
            if cached.status == "completed" and not cached.errors:
                return cached.result

        result = DecisionResult(decision_id=decision_id)

        try:
            expression = decision.get("expression")
            if expression:
                result.result = self.literal_evaluator.evaluate(expression, context)
                self._decision_cache[decision_id] = result
                return result.result

            decision_table = decision.get("decisionTable")
            if decision_table:
                table_result = self._evaluate_decision_table(decision_table, context, decision_id)
                result.result = table_result
                result.status = "completed"
                self._decision_cache[decision_id] = result
                return result.result

            literal_expression = decision.get("literalExpression")
            if literal_expression:
                text = literal_expression.get("text", "")
                result.result = self.literal_evaluator.evaluate(text, context)
                self._decision_cache[decision_id] = result
                return result.result

            invocation = decision.get("invocation")
            if invocation:
                inv_result = await self.invocation_handler.invoke(invocation, context)
                result.result = inv_result
                result.status = "completed"
                self._decision_cache[decision_id] = result
                return result.result

            required_decisions = decision.get("requiredDecisions", [])
            resolved_decisions: dict[str, Any] = {}
            for req_id in required_decisions:
                resolved_decisions[req_id] = context.get(req_id)

            logger.info("Decision %s evaluated with %d resolved dependencies", decision_id, len(resolved_decisions))
            result.result = resolved_decisions if resolved_decisions else None
            result.status = "completed"
            self._decision_cache[decision_id] = result
            return result.result

        except Exception as e:
            result.status = "failed"
            result.errors.append(str(e))
            logger.error("DMN decision %s failed: %s", decision_id, e)
            self._decision_cache[decision_id] = result
            raise

    def _evaluate_decision_table(
        self,
        decision_table: dict[str, Any],
        context: dict[str, Any],
        decision_id: str,
    ) -> Any:
        inputs = decision_table.get("input", [])
        outputs = decision_table.get("output", [])
        rules = decision_table.get("rules", [])

        hit_policy_str = decision_table.get("hitPolicy", "UNIQUE")
        hit_policy = self.hit_policy_handler.parse(hit_policy_str)

        input_values: list[Any] = []
        for inp in inputs:
            expr = inp.get("inputExpression", {})
            text = expr.get("text", "")
            variable_name = expr.get("variable", {}).get("name", text)
            value = context.get(variable_name)
            allowed = inp.get("inputValues")
            if allowed is not None:
                if value not in allowed:
                    value = None
            input_values.append(value)

        matched_rules: list[dict[str, Any]] = []
        for rule in rules:
            entry_matches = True
            j = 0
            for inp_entry in rule.get("inputEntry", []):
                if j < len(input_values):
                    test = inp_entry.get("text", "-")
                    if test != "-" and test != "*":
                        if input_values[j] is not None:
                            try:
                                if str(input_values[j]) != eval(test, {"__builtins__": {}}, {}):
                                    entry_matches = False
                                    break
                            except Exception:
                                if str(input_values[j]) != test:
                                    entry_matches = False
                                    break
                    j += 1
            if entry_matches:
                output_values: dict[str, Any] = {}
                for k, out_entry in enumerate(rule.get("outputEntry", [])):
                    if k < len(outputs):
                        out_name = outputs[k].get("name", f"output_{k}")
                        text = out_entry.get("text", "")
                        if text:
                            try:
                                output_values[out_name] = eval(text, {"__builtins__": {}}, context)
                            except Exception:
                                output_values[out_name] = text
                matched_rules.append({"rule_id": rule.get("id", ""), "output": output_values})

        if not matched_rules:
            return None

        return self.hit_policy_handler.apply(hit_policy, matched_rules)

    def clear_cache(self) -> None:
        self._decision_cache.clear()

    def get_cache_results(self) -> dict[str, DecisionResult]:
        return dict(self._decision_cache)
