from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from engines.document.parsers.base import BaseDocumentParser, ParseOptions, ParseResult
from engines.document.models.media_types import MEDIA_TYPES
from engines.document.models.ksdm_models import UnifiedBiAggregationDocument


class TableauHyperParser(BaseDocumentParser):
    name = "tableau_hyper_bi"
    supported_extensions = (".hyper",)

    async def parse_bytes(self, data: bytes, document_id: str, source_name: str, metadata: dict[str, Any] | None = None, options: ParseOptions | None = None) -> UnifiedBiAggregationDocument:
        raise NotImplementedError(
            "Tableau .hyper is a binary format requiring the Tableau Hyper API Python library. "
            "Install `pip install tableauhyperapi` and use the TableauHyperParser with a file path."
        )

    async def parse_path(self, path: str | Path, document_id: str, metadata: dict[str, Any] | None = None, options: ParseOptions | None = None) -> UnifiedBiAggregationDocument:
        try:
            import importlib as _il
            _th = _il.import_module('tableauhyperapi')
        except ImportError:
            raise ImportError(
                "tableauhyperapi is required to parse Tableau .hyper files. "
                "Install with: pip install tableauhyperapi"
            )

        p = Path(path)
        with _th.HyperProcess(_th.Telemetry.SEND_USAGE_DATA_TELEMETRY_DISABLED) as hyper:
            with _th.Connection(endpoint=hyper.endpoint, database=str(path)) as conn:
                tables = conn.catalog.get_table_names()
                sources = []
                for schema_table in tables:
                    src_name = ".".join(str(p) for p in schema_table)
                    sources.append({"name": src_name, "source_type": "hyper_table"})

                from engines.document.models.ksdm_models import AggregationSource, Dimension, Measure, DimensionAttribute
                doc_sources = [AggregationSource(name=s["name"], source_type=s["source_type"]) for s in sources]

                return UnifiedBiAggregationDocument(
                    name=p.stem,
                    description=f"Tableau Hyper Extract: {p.name}",
                    sources=doc_sources,
                    title=p.stem,
                    document_id=p.stem,
                    media_type=MEDIA_TYPES["tableau_hyper"],
                )

    async def parse_stream(self, stream: AsyncIterator[bytes], document_id: str, source_name: str, metadata: dict[str, Any] | None = None, options: ParseOptions | None = None) -> UnifiedBiAggregationDocument:
        raise NotImplementedError("Tableau .hyper cannot be parsed from a stream (binary format). Use parse_path with a file.")

    def can_parse(self, source: str | Path) -> bool:
        if isinstance(source, str) and source.endswith(".hyper"):
            return True
        try:
            path = Path(source)
            return path.exists() and path.suffix == ".hyper"
        except Exception:
            return False
