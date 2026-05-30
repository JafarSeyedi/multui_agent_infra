"""Decision table evaluator with simple hit policy handling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .hit_policy_handler import HitPolicy, apply_hit_policy


@dataclass(frozen=True)
class DecisionTableEvaluator:
    default_policy: HitPolicy = HitPolicy.COLLECT

    def evaluate(self, table: dict[str, Any], context: dict[str, Any]) -> list[dict[str, Any]] | dict[str, Any] | None:
        rows = list(table.get("rows", []))
        if not rows:
            return None

        policy = HitPolicy(table.get("hitPolicy", self.default_policy))
        matches = []
        for row in rows:
            if row.get("enabled", True):
                matches.append(row)
        return apply_hit_policy(policy, matches, context)
