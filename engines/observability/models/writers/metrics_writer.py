# engines/observability/models/writers/metrics_writer.py
from __future__ import annotations

from ..observability_models import MetricPoint


def write_metric_point(point: MetricPoint) -> dict:
    return {"name": point.name, "value": point.value, "tags": point.tags}
