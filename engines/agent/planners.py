from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ThinkingConfig:
    thinking_budget: int = 1024
    include_thoughts: bool = False


class BasePlanner:
    def apply(self, instruction: str) -> str:
        return instruction

    def get_config(self) -> dict[str, Any]:
        return {}


class BuiltInPlanner(BasePlanner):
    def __init__(self, thinking_config: ThinkingConfig | None = None) -> None:
        self.thinking_config = thinking_config or ThinkingConfig()

    def apply(self, instruction: str) -> str:
        return instruction

    def get_config(self) -> dict[str, Any]:
        return {
            "thinking_config": {
                "thinking_budget": self.thinking_config.thinking_budget,
                "include_thoughts": self.thinking_config.include_thoughts,
            },
        }


class PlanReActPlanner(BasePlanner):
    def apply(self, instruction: str) -> str:
        return (
            f"{instruction}\n\n"
            "You must follow this structure:\n"
            "1. **Plan**: Outline the steps needed to answer.\n"
            "2. **Action**: Execute each step (call tools, search, calculate).\n"
            "3. **Reasoning**: Explain your reasoning for each action.\n"
            "4. **Final Answer**: Provide the final response."
        )

    def get_config(self) -> dict[str, Any]:
        return {
            "planner_type": "plan_react",
        }
