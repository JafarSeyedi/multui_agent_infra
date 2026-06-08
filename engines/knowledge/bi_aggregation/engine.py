"""
BI Aggregator for Insights Layer (Aggregated Analytics)
======================================================
Periodic jobs that compute summaries from stored data and push results 
into a searchable format (ISDM documents).
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, cast

from engines.document.models.ksdm_models import KSDMMetricsDocument, Metric, MetricType, TimeGranularity
from engines.document.models.media_types import MEDIA_TYPES, MediaType
from engines.document.parsers.base import BaseDocumentParser
from engines.document.writers.base import BaseDocumentWriter, WriteResult


class BiAggregationEngine:
    """
    Engine that computes metrics from data sources and produces ISDM documents.
    In a real implementation, this would connect to actual data stores.
    """

    def __init__(self, schedule: str = "@daily"):
        self.schedule = schedule
        self._parsers: Dict[str, BaseDocumentParser] = {}
        self._writers: Dict[str, BaseDocumentWriter] = {}
        self.data_sources: Dict[str, Any] = {}

    def register_parser(self, fmt: str, parser: BaseDocumentParser) -> None:
        self._parsers[fmt] = parser

    def register_writer(self, fmt: str, writer: BaseDocumentWriter) -> None:
        self._writers[fmt] = writer

    async def parse(self, source: str, fmt: str | None = None, **options: Any) -> KSDMMetricsDocument:
        parser = cast(Any, self._parsers.get(fmt or "xmla_discover_xml"))
        if parser is None:
            raise NotImplementedError("No parser registered for the requested format.")
        return parser.parse(source, **options).document

    async def write(self, document: KSDMMetricsDocument, destination: str, fmt: str | None = None, **options: Any) -> WriteResult:
        writer = cast(Any, self._writers.get(fmt or "xmla_discover_xml"))
        if writer is None:
            raise NotImplementedError("No writer registered for the requested format.")
        await writer.write(document, destination, **options)
        return WriteResult(metadata={"destination": destination, "format": fmt})

    async def run_aggregation_job(self) -> KSDMMetricsDocument:
        """
        Run an aggregation job and return a metrics document with the results.
        """
        now = datetime.utcnow()

        metrics = [
            Metric(
                name="entity_count",
                type=MetricType.GAUGE,
                value=42,
                labels={"entity_type": "Person"},
                timestamp=now,
            ),
            Metric(
                name="relation_count",
                type=MetricType.GAUGE,
                value=128,
                labels={"relation_type": "worksFor"},
                timestamp=now,
            ),
            Metric(
                name="avg_entity_confidence",
                type=MetricType.GAUGE,
                value=0.87,
                labels={},
                timestamp=now,
            ),
        ]

        insights_doc = KSDMMetricsDocument(
            title=f"BI Aggregation Job - {now.isoformat()}",
            document_id=f"bi_agg_{now.strftime('%Y%m%d_%H%M%S')}",
            start_time=now - timedelta(days=1),
            end_time=now,
            granularity=TimeGranularity.DAY,
            dimensions=["entity_type", "relation_type"],
            metrics=metrics,
            data_rows=[],
            source_info={
                "job_type": "bi_aggregator",
                "schedule": self.schedule,
                "data_sources": list(self.data_sources.keys()),
            },
            media_type=cast(MediaType, MEDIA_TYPES.get("json")),
        )

        return insights_doc

    async def start_scheduler(self):
        """
        Start a periodic scheduler based on the schedule string.
        This is a simplified version; in production, use a proper scheduler like APScheduler.
        """
        while True:
            await self.run_aggregation_job()
            if self.schedule == "@daily":
                await asyncio.sleep(24 * 60 * 60)
            elif self.schedule == "@hourly":
                await asyncio.sleep(60 * 60)
            else:
                await asyncio.sleep(24 * 60 * 60)


# Backward compatibility alias
BI_Aggregator = BiAggregationEngine
