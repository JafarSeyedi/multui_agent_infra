from __future__ import annotations

from typing import Any

from engines.document.models.ksdm_models import (
    AggregationDefinition,
    AggregationRelationship,
    AggregationSource,
    Dimension,
    Measure,
    UnifiedBiAggregationDocument,
)
from engines.document.model_tools.model_standard_converters.ksdm_bi_converter import BiAggregationConverter
from engines.document.parsers.base import BaseDocumentParser
from engines.document.parsers.ksdm_parsers.bi_aggregation import (
    AwxmlParser,
    CalciteParser,
    CdmParser,
    CognosFmfParser,
    CwmParser,
    MondrianSchemaParser,
    SapCdsParser,
    TableauHyperParser,
    TmslParser,
)
from engines.document.writers.base import BaseDocumentWriter
from engines.document.writers.ksdm_writers.bi_aggregation import (
    AwxmlWriter,
    CalciteWriter,
    CdmWriter,
    CognosFmfWriter,
    CwmWriter,
    MondrianSchemaWriter,
    SapCdsWriter,
    TableauHyperWriter,
    TmslWriter,
)


_PARSER_MAP: dict[str, type[BaseDocumentParser]] = {
    "cwm": CwmParser,
    "mondrian": MondrianSchemaParser,
    "tmsl": TmslParser,
    "cdm": CdmParser,
    "calcite": CalciteParser,
    "awxml": AwxmlParser,
    "sap_cds": SapCdsParser,
    "cognos_fmf": CognosFmfParser,
    "tableau_hyper": TableauHyperParser,
}

_WRITER_MAP: dict[str, type[BaseDocumentWriter]] = {
    "cwm": CwmWriter,
    "mondrian": MondrianSchemaWriter,
    "tmsl": TmslWriter,
    "cdm": CdmWriter,
    "calcite": CalciteWriter,
    "awxml": AwxmlWriter,
    "sap_cds": SapCdsWriter,
    "cognos_fmf": CognosFmfWriter,
    "tableau_hyper": TableauHyperWriter,
}


class BiAggregationEngine:
    def __init__(self, doc: UnifiedBiAggregationDocument | None = None):
        self._doc = doc

    async def async_load(
        self,
        source: str | bytes,
        parser_name: str | None = None,
        **options: Any,
    ) -> UnifiedBiAggregationDocument:
        if parser_name and parser_name in _PARSER_MAP:
            parser = _PARSER_MAP[parser_name]()
        else:
            parser = self._detect_parser(source)
        if isinstance(source, str):
            from pathlib import Path
            path = Path(source)
            result = await parser.parse_path(path, "load")
        else:
            result = await parser.parse_bytes(source, "load", "load")
        assert isinstance(result, UnifiedBiAggregationDocument)
        self._doc = result
        return self._doc

    def load(
        self,
        source: str | bytes,
        parser_name: str | None = None,
        **options: Any,
    ) -> UnifiedBiAggregationDocument:
        import asyncio
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.async_load(source, parser_name, **options))
        raise RuntimeError(
            "Cannot call load() synchronously inside an async context. "
            "Use await engine.async_load() instead."
        )

    def _detect_parser(self, source: str | bytes) -> BaseDocumentParser:
        parsers = list(_PARSER_MAP.values())
        if isinstance(source, str):
            from pathlib import Path
            path = Path(source)
            for p_cls in parsers:
                p = p_cls()
                if p.can_parse(str(path)):
                    return p
        else:
            for p_cls in parsers:
                p = p_cls()
                try:
                    src = source.decode("utf-8", errors="replace")
                    if p.can_parse(src):
                        return p
                except Exception:
                    continue
        raise ValueError(
            "Cannot auto-detect parser for source. Specify parser_name: "
            f"{', '.join(_PARSER_MAP.keys())}"
        )

    def get_cubes(self) -> list[AggregationSource]:
        if self._doc is None:
            return []
        return self._doc.sources

    def get_dimensions(self, cube_name: str | None = None) -> list[Dimension]:
        if self._doc is None:
            return []
        if cube_name is not None:
            return [d for d in self._doc.dimensions if d.source_table == cube_name]
        return self._doc.dimensions

    def get_measures(self, cube_name: str | None = None) -> list[Measure]:
        if self._doc is None:
            return []
        if cube_name is not None:
            self._get_source(cube_name)
        return self._doc.measures

    def _get_source(self, name: str) -> AggregationSource | None:
        if self._doc is None:
            return None
        return next((s for s in self._doc.sources if s.name == name), None)

    def get_relationships(self) -> list[AggregationRelationship]:
        if self._doc is None:
            return []
        return self._doc.relationships

    def get_aggregations(self) -> list[AggregationDefinition]:
        if self._doc is None:
            return []
        return self._doc.aggregations

    def aggregate(
        self,
        group_by: list[str],
        measures: list[str],
        source: str | None = None,
        filter_expr: str | None = None,
        materialized: bool = False,
    ) -> AggregationDefinition:
        agg = AggregationDefinition(
            name=f"agg_{'_'.join(measures)}_{'_'.join(group_by)}",
            source=source or "",
            group_by=group_by,
            measures=measures,
            filter_expression=filter_expr,
            materialized=materialized,
        )
        if self._doc is not None:
            self._doc.aggregations.append(agg)
        return agg

    async def async_convert(self, target_format: str, **options: Any) -> bytes:
        if self._doc is None:
            raise ValueError("No document loaded. Call async_load() first.")
        writer_cls = _WRITER_MAP.get(target_format)
        if writer_cls is None:
            raise ValueError(
                f"Unknown target format: {target_format}. "
                f"Choose from: {', '.join(_WRITER_MAP.keys())}"
            )
        writer = writer_cls()
        return await writer.write(self._doc)

    def convert(self, target_format: str, **options: Any) -> bytes:
        import asyncio
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.async_convert(target_format, **options))
        raise RuntimeError(
            "Cannot call convert() synchronously inside an async context. "
            "Use await engine.async_convert() instead."
        )

    async def async_write(
        self,
        destination: str,
        format: str | None = None,
        **options: Any,
    ) -> bytes:
        if self._doc is None:
            raise ValueError("No document loaded. Call async_load() first.")
        if format and format in _WRITER_MAP:
            writer = _WRITER_MAP[format]()
        else:
            from pathlib import Path
            ext = Path(destination).suffix.lower()
            matched: list[BaseDocumentWriter] = []
            for cls in _WRITER_MAP.values():
                w = cls()
                if any(ext.endswith(e) for e in w.get_supported_extensions()):
                    matched.append(w)
            writer = matched[0] if matched else MondrianSchemaWriter()
        result = await writer.write(self._doc)
        Path(destination).write_bytes(result)
        return result

    def write(self, destination: str, format: str | None = None, **options: Any) -> bytes:
        import asyncio
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.async_write(destination, format, **options))
        raise RuntimeError(
            "Cannot call write() synchronously inside an async context. "
            "Use await engine.async_write() instead."
        )
