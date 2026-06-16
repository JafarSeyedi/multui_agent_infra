# engines/observability/models/parsers/metrics_parser.py
from __future__ import annotations

from ..observability_models import MetricPoint


def parse_metric_point(data: dict) -> MetricPoint:
    return MetricPoint(
        name=data["name"],
        value=data.get("value", 0.0),
        tags=data.get("tags", {}),
    )
