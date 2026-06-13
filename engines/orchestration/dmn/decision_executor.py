"""DMN decision executor with decision graph traversal and dependency resolution.

Supports decision tables, literal expressions, invocations, and BKM calls
at DMN 1.3 specification level. Works with both dict-based and OSDM-typed
Decision objects.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from ..._types import DmnValue, FeelContext, Metadata, RawData

from ..core.instance import ProcessInstance
from ..core.engine import OrchestrationEngine
from engines.orchestration.models.osdm_models import (
    Decision,
    DecisionTable,
    InputClause,
    OutputClause,
    DecisionRule,
    LiteralExpression,
    UnaryTests,
    FormalExpression,
    Context,
    ContextEntry,
    Relation,
    FunctionDefinition,
    FormalParameter,
    Invocation,
    Binding,
)
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
    decision_table: RawData | None = None
    literal_expression: str | None = None
    required_decisions: list[str] = field(default_factory=list)
    required_inputs: list[str] = field(default_factory=list)
    invoked_bkm: str | None = None
    variable_name: str | None = None


@dataclass
class DecisionResult:
    decision_id: str
    result: DmnValue | None = None
    status: str = "completed"
    errors: list[str] = field(default_factory=list)
    rule_results: list[RawData] = field(default_factory=list)
    hit_policy_applied: str | None = None
    evaluation_time_ms: float = 0.0


_BODY_EXTRACTORS: dict[type, Callable[[Any], str | None]] = {
    FormalExpression: lambda v: v.body,
    LiteralExpression: lambda v: v.body,
    UnaryTests: lambda v: v.body,
    str: lambda v: v,
}


def _get_body(value: Any) -> str | None:
    if value is None:
        return None
    handler = _BODY_EXTRACTORS.get(type(value))
    if handler:
        return handler(value)
    return str(value)


_BOXED_EXPRESSION_HANDLERS: dict[type, Callable[[Any, Any, Any], Any]] = {
    DecisionTable: lambda self, expr, vars: self._evaluate_osdm_decision_table(expr, vars, "boxed"),
    LiteralExpression: lambda self, expr, vars: self.literal_evaluator.evaluate(expr.body or "", vars),
    Context: lambda self, expr, vars: self.evaluate_context(expr, vars),
    Relation: lambda self, expr, vars: self.evaluate_relation(expr, vars),
    Invocation: lambda self, expr, vars: self.evaluate_invocation(expr, vars),
    FunctionDefinition: lambda self, expr, vars: self.evaluate_function_definition(expr, [], vars),
    str: lambda self, expr, vars: self.feel_engine.evaluate(expr, vars),
}


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
        decision: RawData,
        context: FeelContext,
        instance: ProcessInstance | None = None,
    ) -> DmnValue | None:
        decision_id = decision.get("id", "unknown")
        name = decision.get("name", decision_id)
        _variable_name = decision.get("variable", {}).get("name", "decision_result")

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

    async def evaluate_osdm(
        self,
        decision: Decision,
        context: FeelContext,
    ) -> DmnValue | None:
        decision_id = decision.id
        name = decision.name or decision_id

        logger.debug("Evaluating OSDM DMN decision: %s (%s)", name, decision_id)

        if decision_id in self._decision_cache:
            cached = self._decision_cache[decision_id]
            if cached.status == "completed" and not cached.errors:
                return cached.result

        result = DecisionResult(decision_id=decision_id)

        try:
            table = decision.decision_table or decision.table_data
            if table:
                table_result = self._evaluate_osdm_decision_table(table, context, decision_id)
                result.result = table_result
                result.status = "completed"
                self._decision_cache[decision_id] = result
                return result.result

            if decision.expression:
                expr_body = _get_body(decision.expression)
                if expr_body:
                    result.result = self.literal_evaluator.evaluate(expr_body, context)
                    self._decision_cache[decision_id] = result
                    return result.result

            logger.info("OSDM Decision %s evaluated with no table or expression", decision_id)
            result.result = None
            result.status = "completed"
            self._decision_cache[decision_id] = result
            return result.result

        except Exception as e:
            result.status = "failed"
            result.errors.append(str(e))
            logger.error("OSDM DMN decision %s failed: %s", decision_id, e)
            self._decision_cache[decision_id] = result
            raise

    def _evaluate_osdm_decision_table(
        self,
        table: DecisionTable,
        context: FeelContext,
        decision_id: str,
    ) -> DmnValue | None:
        hit_policy_str = table.hit_policy or "UNIQUE"
        hit_policy = self.hit_policy_handler.parse(hit_policy_str)

        input_values: list[DmnValue] = []
        for inp in table.inputs:
            expr = inp.input_expression
            text = _get_body(expr) if expr else ""
            variable_name = text
            value = context.get(variable_name) if variable_name is not None else None
            if inp.input_values is not None:
                if value not in inp.input_values:
                    value = None
            input_values.append(value)

        matched_rules: list[RawData] = []
        for rule in table.rules:
            entry_matches = True
            j = 0
            for inp_entry in rule.input_entries:
                if j < len(input_values):
                    test = _get_body(inp_entry) or "-"
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
                output_values: Metadata = {}
                for k, out_entry in enumerate(rule.output_entries):
                    if k < len(table.outputs):
                        out_name = table.outputs[k].name or f"output_{k}"
                        text = _get_body(out_entry) or ""
                        if text:
                            try:
                                output_values[out_name] = eval(text, {"__builtins__": {}}, context)
                            except Exception:
                                output_values[out_name] = text
                matched_rules.append({"rule_id": rule.id, "output": output_values})

        if not matched_rules:
            return None

        return self.hit_policy_handler.apply(hit_policy, matched_rules)

    def _evaluate_decision_table(
        self,
        decision_table: RawData,
        context: FeelContext,
        decision_id: str,
    ) -> DmnValue | None:
        inputs = decision_table.get("input", [])
        outputs = decision_table.get("output", [])
        rules = decision_table.get("rules", [])

        hit_policy_str = decision_table.get("hitPolicy", "UNIQUE")
        hit_policy = self.hit_policy_handler.parse(hit_policy_str)

        input_values: list[DmnValue] = []
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

        matched_rules: list[RawData] = []
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
                output_values: Metadata = {}
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

    # ── Boxed Expression Evaluation (DMN 1.3 §8.5) ────────────────────

    def evaluate_context(self, context: Context, variables: FeelContext) -> Metadata:
        """Evaluate a DMN context expression (§8.5.1).
        Each entry is evaluated in sequence, with previous entries in scope."""
        result: Metadata = {}
        eval_context = dict(variables)
        for entry in context.entries:
            if entry.value_expression:
                value = self.feel_engine.evaluate(entry.value_expression, eval_context)
            else:
                value = None
            key = entry.key or entry.variable_name or f"entry_{len(result)}"
            result[key] = value
            eval_context[key] = value
        return result

    def evaluate_relation(self, relation: Relation, variables: FeelContext) -> list[Metadata]:
        """Evaluate a DMN relation expression (§8.5.2).
        Each row is evaluated as a set of column values."""
        results = []
        for row in relation.rows:
            row_result = {}
            for i, col_name in enumerate(relation.columns):
                if i < len(row):
                    try:
                        row_result[col_name] = self.feel_engine.evaluate(row[i], variables)
                    except Exception:
                        row_result[col_name] = row[i]
            results.append(row_result)
        return results

    def evaluate_function_definition(
        self, func_def: FunctionDefinition, arguments: list[DmnValue], variables: FeelContext,
    ) -> DmnValue | None:
        """Evaluate a DMN function definition (§8.5.3).
        Bind formal parameters to actual arguments, evaluate body."""
        if not func_def.body_expression:
            return None
        bound_context = dict(variables)
        for i, param in enumerate(func_def.formal_parameters):
            if i < len(arguments):
                bound_context[param.name] = arguments[i]
            elif i < len(arguments) is False:
                bound_context[param.name] = None
        return self.feel_engine.evaluate(func_def.body_expression, bound_context)

    def evaluate_invocation(
        self, invocation: Invocation, variables: FeelContext,
    ) -> DmnValue | None:
        """Evaluate a DMN invocation expression (§8.4).
        Bind actual parameters and call the referenced decision or BKM."""
        # Evaluate binding expressions
        bound_vars = dict(variables)
        for binding in invocation.bindings:
            param_name = binding.parameter or binding.formal_parameter
            if param_name and binding.expression:
                bound_vars[param_name] = self.feel_engine.evaluate(binding.expression, variables)
        # Delegate to the appropriate handler
        if invocation.called_element_type == "bkm":
            return self.invocation_handler._resolve_called_element(
                invocation.called_element_ref, bound_vars,
            )
        else:
            decision_id = invocation.called_element_ref
            if decision_id in self._decision_cache:
                return self._decision_cache[decision_id].result
            return self.invocation_handler._resolve_called_element(
                decision_id, bound_vars,
            )

    def _evaluate_boxed_expression(self, expression: Any, variables: FeelContext,
    ) -> DmnValue | None:
        """Dispatch to the appropriate boxed expression evaluator."""
        handler = _BOXED_EXPRESSION_HANDLERS.get(type(expression))
        if handler:
            return handler(self, expression, variables)
        return expression
