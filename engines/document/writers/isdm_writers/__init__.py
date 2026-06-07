"""ISDM writers."""

from __future__ import annotations

import json
import csv
import io
from engines.document.models.isdm_models import BIAggregation as BIAggregation, BIAggregatorModel, ISDMDocument, Metric as Metric, MetricType as MetricType, TimeGranularity as TimeGranularity


class ISDMJSONWriter:
    """Writer for ISDM JSON format."""
    
    async def write(self, doc: ISDMDocument) -> bytes:
        data = {
            "version": "2.0",
            "granularity": doc.granularity.value if doc.granularity else "day",
            "dimensions": doc.dimensions,
            "metrics": [
                {
                    "name": m.name,
                    "type": m.type.value if m.type else "gauge",
                    "value": m.value,
                    "labels": m.labels,
                    "timestamp": m.timestamp,
                    "buckets": m.buckets,
                    "bucket_counts": m.bucket_counts,
                }
                for m in doc.metrics
            ],
            "data_rows": doc.data_rows,
        }
        return json.dumps(data).encode("utf-8")


class ISDMYAMLWriter:
    """Writer for ISDM YAML format."""
    
    async def write(self, doc: ISDMDocument) -> bytes:
        import yaml
        data = {
            "version": "2.0",
            "granularity": doc.granularity.value if doc.granularity else "day",
            "dimensions": doc.dimensions,
            "metrics": [{"name": m.name, "type": m.type.value if m.type else "gauge"} for m in doc.metrics],
        }
        return yaml.dump(data).encode("utf-8")


class BIAggregatorJSONWriter:
    """Writer for BI Aggregator JSON format."""
    
    async def write(self, doc: BIAggregatorModel) -> bytes:
        data = {
            "version": doc.version,
            "schedule": doc.schedule,
            "aggregations": doc.aggregations,
            "sources": doc.sources,
            "targets": doc.targets,
        }
        return json.dumps(data).encode("utf-8")


class BIAggregatorYAMLWriter:
    """Writer for BI Aggregator YAML format."""
    
    async def write(self, doc: BIAggregatorModel) -> bytes:
        import yaml
        data = {
            "version": doc.version,
            "schedule": doc.schedule,
            "aggregations": doc.aggregations,
        }
        return yaml.dump(data).encode("utf-8")


class MetricsCSVWriter:
    """Writer for Metrics CSV format."""
    
    async def write(self, doc: ISDMDocument) -> bytes:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["metric_name", "type", "value", "timestamp", "labels"])
        for m in doc.metrics:
            labels = ";".join(f"{k}={v}" for k, v in (m.labels or {}).items())
            writer.writerow([m.name, m.type.value if m.type else "", m.value, m.timestamp or "", labels])
        return output.getvalue().encode("utf-8")
