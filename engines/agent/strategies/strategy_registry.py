# agents/orchestration/interaction/strategy_registry.py
from __future__ import annotations

from collections.abc import Iterable
from threading import RLock
from typing import Generic
from typing import TypeVar

from .base_strategy import InteractionStrategy

TStrategy = TypeVar("TStrategy", bound=InteractionStrategy)


class InteractionStrategyRegistry(Generic[TStrategy]):
    """
    Guardian of interaction strategies. Prevents duplicate strategy registration
    Provides auxiliary features like listing and safe removal.
    """

    def __init__(self) -> None:
        self._strategies: dict[str, TStrategy] = {}
        self._lock = RLock()

    def register(self, strategy: TStrategy, *, replace: bool = False) -> TStrategy:
        """
        Registers a new strategy. If duplicate and
        replace=False raises error; otherwise replaces.
        """
        scenario = strategy.scenario_name
        with self._lock:
            if scenario in self._strategies and not replace:
                raise ValueError(f"Strategy for scenario '{scenario}' already registered.")
            self._strategies[scenario] = strategy
        return strategy

    def unregister(self, scenario: str) -> None:
        """Removes strategy with specified scenario name (if exists)."""
        with self._lock:
            self._strategies.pop(scenario, None)

    def get(self, scenario: str) -> TStrategy | None:
        """Returns strategy without error (if registered)."""
        with self._lock:
            return self._strategies.get(scenario)

    def require(self, scenario: str) -> TStrategy:
        """
        Returns strategy or raises meaningful error if not found.
        Useful when strategy presence is required.
        """
        strategy = self.get(scenario)
        if strategy is None:
            raise KeyError(f"No interaction strategy registered for scenario '{scenario}'.")
        return strategy

    def list_scenarios(self) -> list[str]:
        """Returns all registered scenarios."""
        with self._lock:
            return list(self._strategies.keys())

    def all_strategies(self) -> Iterable[TStrategy]:
        """Encyclopedia of all strategies for review or testing."""
        with self._lock:
            return list(self._strategies.values())
