"""CEP aggregator with window aggregation functions.

Supports aggregate functions and grouped aggregations.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from enum import Enum
from typing import Any


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
        if not data:
            if func == "count":
                return 0
            return None

        numeric = [float(v) for v in data if isinstance(v, (int, float))]
        _non_numeric = [v for v in data if not isinstance(v, (int, float))]

        if func == "count":
            return len(data)
        elif func == "sum":
            return sum(numeric) if numeric else 0
        elif func == "avg":
            return statistics.mean(numeric) if numeric else None
        elif func == "min":
            candidates = numeric if numeric else data
            return min(candidates) if candidates else None
        elif func == "max":
            candidates = numeric if numeric else data
            return max(candidates) if candidates else None
        elif func == "median":
            return statistics.median(numeric) if numeric else None
        elif func == "stddev":
            return statistics.stdev(numeric) if len(numeric) >= 2 else None
        elif func == "first":
            return data[0] if data else None
        elif func == "last":
            return data[-1] if data else None
        elif func == "distinctCount":
            return len(set(data))
        else:
            return len(data)

    def register(self, name: str, definition: AggregationDefinition) -> None:
        self._definitions[name] = definition

    def get(self, name: str) -> AggregationDefinition | None:
        return self._definitions.get(name)
