from __future__ import annotations

from typing import Any

from engines.document.models.ksdm_models import UnifiedBiAggregationDocument


class BiAggregationConverter:
    def convert(self, doc: UnifiedBiAggregationDocument, target_format: str, **options) -> bytes:
        from engines.document.writers.ksdm_writers.bi_aggregation import (
            CwmWriter,
            MondrianSchemaWriter,
            XmlaWriter,
            TmslWriter,
            CdmWriter,
            CalciteWriter,
            AwxmlWriter,
            SapCdsWriter,
            CognosFmfWriter,
        )

        writer_map = {
            "cwm": CwmWriter,
            "mondrian": MondrianSchemaWriter,
            "xmla": XmlaWriter,
            "tmsl": TmslWriter,
            "cdm": CdmWriter,
            "calcite": CalciteWriter,
            "awxml": AwxmlWriter,
            "sap_cds": SapCdsWriter,
            "cognos_fmf": CognosFmfWriter,
        }

        cls: Any = writer_map.get(target_format)
        if cls is None:
            raise ValueError(f"Unknown target format: {target_format}")
        import asyncio
        return asyncio.run(cls().write(doc))
