"""Decision table evaluator with full DMN 1.3 semantics.

Supports input/output clauses, rule matching, types, and annotations.
Handles all DMN hit policies: UNIQUE, FIRST, PRIORITY, ANY, COLLECT,
OUTPUT_ORDER, RULE_ORDER.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .hit_policy_handler import HitPolicy, apply_hit_policy


class HitPolicyType(str, Enum):
    UNIQUE = "UNIQUE"
    FIRST = "FIRST"
    PRIORITY = "PRIORITY"
    ANY = "ANY"
    COLLECT = "COLLECT"
    OUTPUT_ORDER = "OUTPUT_ORDER"
    RULE_ORDER = "RULE_ORDER"


@dataclass
class InputClause:
    input_expression: str = ""
    input_values: list[Any] | None = None
    label: str | None = None
    allowed_values: list[Any] | None = None


@dataclass
class OutputClause:
    name: str = ""
    output_values: list[Any] | None = None
    default_output: Any = None
    label: str | None = None
    type_ref: str = "string"


@dataclass
class DecisionRule:
    rule_id: str = ""
    input_entries: list[str] = field(default_factory=list)
    output_entries: list[str] = field(default_factory=list)
    annotation_entries: list[str] = field(default_factory=list)
    input_values: list[Any] = field(default_factory=list)
    output_values: dict[str, Any] = field(default_factory=dict)
    is_matched: bool = False
    priority: int = 0


@dataclass
class DecisionTable:
    table_id: str = ""
    name: str | None = None
    hit_policy: str = "UNIQUE"
    aggregation: str | None = None
    preferred_orientation: str = "Rule-as-Row"
    inputs: list[InputClause] = field(default_factory=list)
    outputs: list[OutputClause] = field(default_factory=list)
    rules: list[DecisionRule] = field(default_factory=list)
    annotations: list[str] = field(default_factory=list)


class DecisionTableEvaluator:
    def __init__(self, default_policy: HitPolicy = HitPolicy.COLLECT) -> None:
        self.default_policy = default_policy

    def evaluate(
        self,
        table: dict[str, Any],
        context: dict[str, Any],
    ) -> list[dict[str, Any]] | dict[str, Any] | None:
        decision_table = self._normalize_table(table)
        input_values = self._resolve_input_values(decision_table, context)
        matched_rules = self._match_rules(decision_table, input_values, context)

        if not matched_rules:
            return self._apply_default_outputs(decision_table)

        policy = HitPolicy(table.get("hitPolicy", self.default_policy.value))
        return apply_hit_policy(policy, matched_rules, context)

    def _normalize_table(self, table: dict[str, Any]) -> DecisionTable:
        result = DecisionTable()
        result.table_id = table.get("id", table.get("name", ""))
        result.name = table.get("name")
        result.hit_policy = table.get("hitPolicy", "UNIQUE")
        result.aggregation = table.get("aggregation")
        result.preferred_orientation = table.get("preferredOrientation", "Rule-as-Row")

        for inp in table.get("inputs", table.get("input", [])):
            clause = InputClause(
                input_expression=inp.get("inputExpression", {}).get("text", inp.get("expression", "")),
                input_values=inp.get("inputValues", []),
                label=inp.get("label"),
            )
            result.inputs.append(clause)

        for out in table.get("outputs", table.get("output", [])):
            out_clause = OutputClause(
                name=out.get("name", ""),
                output_values=out.get("outputValues", []),
                default_output=out.get("defaultOutputEntry"),
                label=out.get("label"),
                type_ref=out.get("typeRef", "string"),
            )
            result.outputs.append(out_clause)

        for rule_data in table.get("rules", table.get("rows", [])):
            rule = DecisionRule(
                rule_id=rule_data.get("id", ""),
                input_entries=rule_data.get("inputEntry", []),
                output_entries=rule_data.get("outputEntry", []),
                annotation_entries=rule_data.get("annotationEntry", []),
            )
            result.rules.append(rule)

        return result

    def _resolve_input_values(
        self,
        table: DecisionTable,
        context: dict[str, Any],
    ) -> list[Any]:
        values: list[Any] = []
        for clause in table.inputs:
            value = context.get(clause.input_expression)
            if value is None and not clause.input_expression:
                values.append(None)
                continue

            if clause.allowed_values is not None:
                if value not in clause.allowed_values:
                    values.append(None)
                    continue

            values.append(value)
        return values

    def _match_rules(
        self,
        table: DecisionTable,
        input_values: list[Any],
        context: dict[str, Any],
    ) -> list[dict[str, Any]]:
        matched: list[dict[str, Any]] = []

        for rule in table.rules:
            rule.input_values = []
            rule.output_values = {}
            rule.is_matched = True

            for i, entry_text in enumerate(rule.input_entries):
                if i < len(input_values):
                    if not self._test_input_entry(entry_text, input_values[i], context):
                        rule.is_matched = False
                        break
                    rule.input_values.append(input_values[i])

            if rule.is_matched:
                for j, out_text in enumerate(rule.output_entries):
                    if j < len(table.outputs):
                        out_name = table.outputs[j].name
                        if out_text.strip():
                            try:
                                rule.output_values[out_name] = eval(out_text.strip(), {"__builtins__": {}}, context)
                            except Exception:
                                rule.output_values[out_name] = out_text.strip()
                        else:
                            default = table.outputs[j].default_output
                            rule.output_values[out_name] = default.strip() if default else None

                matched.append({
                    "rule_id": rule.rule_id,
                    "output_values": rule.output_values,
                    "priority": rule.priority,
                })

        return matched

    def _test_input_entry(self, entry_text: str, input_value: Any, context: dict[str, Any]) -> bool:
        text = entry_text.strip()
        if not text or text == "-" or text == "*":
            return True

        if text.startswith("[") and text.endswith("]"):
            try:
                allowed = eval(text, {"__builtins__": {}}, {})
                if isinstance(allowed, list):
                    return input_value in allowed
            except Exception:
                pass
            return False

        if text.startswith("(") and text.endswith(")"):
            inner = text[1:-1].strip()
            parts = inner.split(",")
            if len(parts) == 2:
                lo = self._parse_bound(parts[0].strip(), context)
                hi = self._parse_bound(parts[1].strip(), context)
                if lo is not None and hi is not None and input_value is not None:
                    try:
                        return float(lo) < float(input_value) < float(hi)
                    except (ValueError, TypeError):
                        pass
            return False

        if text.endswith(")") and (".." in text):
            idx = text.find("..")
            if idx > 0:
                lo_str = text[:idx].strip()
                if lo_str.endswith("(") or lo_str.endswith("["):
                    lo_str = lo_str[:-1].strip()
                hi_str = text[idx + 2:].strip()
                if hi_str.startswith(")") or hi_str.startswith("]"):
                    hi_str = hi_str[1:].strip()
                lo = self._parse_bound(lo_str, context)
                hi = self._parse_bound(hi_str, context)
                if lo is not None and hi is not None and input_value is not None:
                    try:
                        return float(lo) <= float(input_value) <= float(hi)
                    except (ValueError, TypeError):
                        pass

        if input_value is not None:
            return str(input_value) == text

        return False

    def _parse_bound(self, text: str, context: dict[str, Any]) -> Any:
        text = text.strip()
        try:
            return float(text) if "." in text else int(text)
        except ValueError:
            return context.get(text)

    def _apply_default_outputs(self, table: DecisionTable) -> dict[str, Any] | None:
        has_defaults = any(clause.default_output is not None for clause in table.outputs)
        if not has_defaults:
            return None
        result: dict[str, Any] = {}
        for clause in table.outputs:
            if clause.default_output is not None:
                result[clause.name] = clause.default_output
        return result if result else None
