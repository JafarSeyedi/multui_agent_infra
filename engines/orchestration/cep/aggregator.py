"""Aggregation functions for CEP windows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Aggregation:
    name: str
    func: Callable[[list[float]], float]

    def compute(self, values: list[float]) -> float:
        return self.func(values)


class Aggregator:
    @staticmethod
    def sum(values: list[float]) -> float:
        return sum(values)

    @staticmethod
    def avg(values: list[float]) -> float:
        return (sum(values) / len(values)) if values else 0.0

    @staticmethod
    def count(values: list[float]) -> float:
        return float(len(values))

    @staticmethod
    def min(values: list[float]) -> float:
        return min(values) if values else 0.0

    @staticmethod
    def max(values: list[float]) -> float:
        return max(values) if values else 0.0
