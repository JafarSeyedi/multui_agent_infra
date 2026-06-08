from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from engines.document.models.ksdm_models import BIAggregatorModel
from ..base import BaseDocumentParser, ParseOptions
from .bi_json import BIAggregatorJSONParser


class BIAggregatorYAMLParser(BaseDocumentParser):
    name = "bi_aggregator_yaml"
    supported_extensions = [".bi.yaml"]

    async def parse_bytes(
        self, data: bytes, document_id: str, source_name: str,
        metadata: dict[str, Any] | None = None,
        options: ParseOptions | None = None,
    ) -> BIAggregatorModel:
        raw = yaml.safe_load(data.decode("utf-8"))
        return await BIAggregatorJSONParser().parse_bytes(
            json.dumps(raw).encode("utf-8"), document_id, source_name
        )

    async def parse_path(
        self, path: str | Path, document_id: str,
        metadata: dict[str, Any] | None = None,
        options: ParseOptions | None = None,
    ) -> BIAggregatorModel:
        p = Path(path)
        return await self.parse_bytes(p.read_bytes(), document_id, p.name)

    async def parse_stream(self, stream, document_id: str,
                           source_name: str, metadata=None, options=None) -> BIAggregatorModel:
        data = b"".join([chunk async for chunk in stream])
        return await self.parse_bytes(data, document_id, source_name)
