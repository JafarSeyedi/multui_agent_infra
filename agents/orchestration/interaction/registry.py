# agents/orchestration/interaction/registry.py
from typing import Dict, Type
from .base_strategy import BaseInteractionStrategy

class InteractionStrategyRegistry:
    def __init__(self):
        self._strategies: Dict[str, BaseInteractionStrategy] = {}

    def register(self, strategy: BaseInteractionStrategy) -> BaseInteractionStrategy:
        scenario = strategy.scenario
        if scenario in self._strategies:
            raise ValueError(f"Strategy for scenario '{scenario}' already registered.")
        self._strategies[scenario] = strategy
        return strategy

    def get(self, scenario: str) -> BaseInteractionStrategy | None:
        return self._strategies.get(scenario)

    def require(self, scenario: str) -> BaseInteractionStrategy:
        strategy = self.get(scenario)
        if strategy is None:
            raise KeyError(f"No interaction strategy registered for scenario '{scenario}'.")
        return strategy
