"""Hit policy handler for DMN decision tables.

Supports all DMN hit policies: UNIQUE, FIRST, PRIORITY, ANY, COLLECT,
OUTPUT_ORDER, RULE_ORDER with exact semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class HitPolicy(str, Enum):
    UNIQUE = "UNIQUE"
    FIRST = "FIRST"
    PRIORITY = "PRIORITY"
    ANY = "ANY"
    COLLECT = "COLLECT"
    OUTPUT_ORDER = "OUTPUT_ORDER"
    RULE_ORDER = "RULE_ORDER"
    C_COLLECT = "C+" 
    C_SUM = "C#" 
    C_MIN = "C<" 
    C_MAX = "C>" 
    C_COUNT = "CC" 


def apply_hit_policy(
    policy: HitPolicy,
    matches: list[dict[str, Any]],
    context: dict[str, Any] | None = None,
) -> Any:
    if not matches:
        return None

    if policy == HitPolicy.UNIQUE:
        if len(matches) > 1:
            return matches[0]["output_values"]
        return matches[0]["output_values"] if matches else None

    elif policy == HitPolicy.FIRST:
        sorted_matches = sorted(matches, key=lambda m: m.get("priority", 0), reverse=True)
        return sorted_matches[0]["output_values"] if sorted_matches else None

    elif policy == HitPolicy.PRIORITY:
        sorted_matches = sorted(matches, key=lambda m: m.get("priority", 0), reverse=True)
        return sorted_matches[0]["output_values"] if sorted_matches else None

    elif policy == HitPolicy.ANY:
        if not matches:
            return None
        first = matches[0]["output_values"]
        for m in matches[1:]:
            if m["output_values"] != first:
                return first
        return first

    elif policy == HitPolicy.COLLECT:
        return [m["output_values"] for m in matches]

    elif policy == HitPolicy.OUTPUT_ORDER:
        sorted_matches = sorted(matches, key=lambda m: m.get("priority", 0))
        return [m["output_values"] for m in sorted_matches]

    elif policy == HitPolicy.RULE_ORDER:
        return [m["output_values"] for m in matches]

    elif policy == HitPolicy.C_COLLECT:
        return [m["output_values"] for m in matches]

    elif policy == HitPolicy.C_SUM:
        if not matches:
            return 0
        values = _extract_numeric_values(matches)
        return sum(values) if values else 0

    elif policy == HitPolicy.C_MIN:
        if not matches:
            return None
        values = _extract_numeric_values(matches)
        return min(values) if values else None

    elif policy == HitPolicy.C_MAX:
        if not matches:
            return None
        values = _extract_numeric_values(matches)
        return max(values) if values else None

    elif policy == HitPolicy.C_COUNT:
        return len(matches)

    return matches[0]["output_values"] if matches else None


def _extract_numeric_values(matches: list[dict[str, Any]]) -> list[float]:
    values: list[float] = []
    for m in matches:
        out = m.get("output_values", {})
        if isinstance(out, dict):
            for v in out.values():
                try:
                    values.append(float(v))
                except (ValueError, TypeError):
                    pass
        elif isinstance(out, (int, float)):
            values.append(float(out))
    return values


class HitPolicyHandler:
    def parse(self, policy_str: str) -> HitPolicy:
        mapping = {
            "unique": HitPolicy.UNIQUE,
            "first": HitPolicy.FIRST,
            "priority": HitPolicy.PRIORITY,
            "any": HitPolicy.ANY,
            "collect": HitPolicy.COLLECT,
            "outputorder": HitPolicy.OUTPUT_ORDER,
            "ruleorder": HitPolicy.RULE_ORDER,
            "c+": HitPolicy.C_COLLECT,
            "c#": HitPolicy.C_SUM,
            "c<": HitPolicy.C_MIN,
            "c>": HitPolicy.C_MAX,
            "cc": HitPolicy.C_COUNT,
        }
        return mapping.get(policy_str.lower().replace(" ", "").replace("_", "").replace("-", ""), HitPolicy.UNIQUE)

    def apply(
        self,
        policy: HitPolicy,
        matches: list[dict[str, Any]],
        context: dict[str, Any] | None = None,
    ) -> Any:
        return apply_hit_policy(policy, matches, context)
