"""Business rule integration bridge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class BusinessRuleAdapter:
    """Execute a callable rule and return resulting payload."""

    fn: Callable[[dict[str, Any]], Any]

    def invoke(self, context: dict[str, Any]) -> Any:
        return self.fn(context)
