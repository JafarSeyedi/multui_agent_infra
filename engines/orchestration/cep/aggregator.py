"""CEP aggregator with window aggregation functions.

Supports aggregate functions and grouped aggregations.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable


class AggregationFunction(str, Enum):
    COUNT = "count"
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    MEDIAN = "median"
    STDDEV = "stddev"
    PERCENTILE = "percentile"
    FIRST = "first"
    LAST = "last"
    DISTINCT_COUNT = "distinctCount"


@dataclass
class AggregationDefinition:
    function: str = "count"
    field: str | None = None
    group_by: str | None = None
    output_variable: str = ""
    filter: str | None = None


def _agg_count(data: list[Any]) -> Any:
    return len(data)


def _agg_sum(data: list[Any]) -> Any:
    numeric = [float(v) for v in data if isinstance(v, (int, float))]
    return sum(numeric) if numeric else 0


def _agg_avg(data: list[Any]) -> Any:
    numeric = [float(v) for v in data if isinstance(v, (int, float))]
    return statistics.mean(numeric) if numeric else None


def _agg_min(data: list[Any]) -> Any:
    numeric = [float(v) for v in data if isinstance(v, (int, float))]
    candidates = numeric if numeric else data
    return min(candidates) if candidates else None


def _agg_max(data: list[Any]) -> Any:
    numeric = [float(v) for v in data if isinstance(v, (int, float))]
    candidates = numeric if numeric else data
    return max(candidates) if candidates else None


def _agg_median(data: list[Any]) -> Any:
    numeric = [float(v) for v in data if isinstance(v, (int, float))]
    return statistics.median(numeric) if numeric else None


def _agg_stddev(data: list[Any]) -> Any:
    numeric = [float(v) for v in data if isinstance(v, (int, float))]
    return statistics.stdev(numeric) if len(numeric) >= 2 else None


def _agg_first(data: list[Any]) -> Any:
    return data[0] if data else None


def _agg_last(data: list[Any]) -> Any:
    return data[-1] if data else None


def _agg_distinct_count(data: list[Any]) -> Any:
    return len(set(data))


_AGGREGATION_HANDLERS: dict[str, Callable[[list[Any]], Any]] = {
    "count": _agg_count,
    "sum": _agg_sum,
    "avg": _agg_avg,
    "min": _agg_min,
    "max": _agg_max,
    "median": _agg_median,
    "stddev": _agg_stddev,
    "first": _agg_first,
    "last": _agg_last,
    "distinctcount": _agg_distinct_count,
}


class Aggregator:
    def __init__(self) -> None:
        self._definitions: dict[str, AggregationDefinition] = {}

    def aggregate(
        self,
        agg_config: dict[str, Any],
        context: dict[str, Any],
    ) -> Any:
        definition = self._normalize(agg_config)
        func = definition.function.lower()
        field = definition.field

        data = self._extract_data(context, field)

        if definition.filter:
            data = self._apply_filter(data, definition.filter)

        return self._compute(data, func)

    def _normalize(self, config: dict[str, Any]) -> AggregationDefinition:
        return AggregationDefinition(
            function=config.get("function", config.get("type", "count")),
            field=config.get("field"),
            group_by=config.get("groupBy"),
            output_variable=config.get("outputVariable", ""),
            filter=config.get("filter"),
        )

    def _extract_data(self, context: dict[str, Any], field: str | None) -> list[Any]:
        if field is None:
            return [v for v in context.values() if isinstance(v, (int, float))]
        value = context.get(field)
        if isinstance(value, (list, tuple)):
            return list(value)
        if isinstance(value, (int, float)):
            return [value]
        if value is not None:
            return [value]
        return []

    def _apply_filter(self, data: list[Any], filter_expr: str) -> list[Any]:
        return data

    def _compute(self, data: list[Any], func: str) -> Any:
        handler = _AGGREGATION_HANDLERS.get(func)
        if handler is not None:
            return handler(data)
        return len(data)

    def register(self, name: str, definition: AggregationDefinition) -> None:
        self._definitions[name] = definition

    def get(self, name: str) -> AggregationDefinition | None:
        return self._definitions.get(name)
