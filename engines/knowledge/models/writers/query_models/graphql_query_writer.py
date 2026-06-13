from __future__ import annotations

import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, BinaryIO, TextIO, cast

from engines.knowledge.models.query_models import (
    UnifiedQueryDocument,
    GraphqlQueryDocument,
    GraphqlOperation,
    GraphqlField,
    GraphqlError,
)
from engines.document.writers.base import BaseDocument, BaseDocumentWriter


class GraphqlQueryWriter(BaseDocumentWriter):
    supported_format = None

    def can_write(self, document) -> bool:
        return isinstance(document, UnifiedQueryDocument) and document.graphql is not None

    async def write(self, document: BaseDocument, destination: str | Path | BinaryIO | TextIO | None = None, **options: Any) -> bytes:
        doc = cast(UnifiedQueryDocument, document)
        gql = doc.graphql or GraphqlQueryDocument()

        if gql.query_text:
            text = gql.query_text
        elif gql.operations or gql.response_data or gql.response_errors:
            payload: dict[str, Any] = {}
            if gql.response_data:
                payload["data"] = gql.response_data
            if gql.response_errors:
                payload["errors"] = [{"message": e.message, "locations": e.locations, "path": e.path} for e in gql.response_errors]
            text = json.dumps(payload, indent=2)
        else:
            text = ""

        result = text.encode("utf-8")
        if destination is not None:
            if isinstance(destination, (str, Path)):
                Path(destination).write_bytes(result)
            else:
                cast(BinaryIO, destination).write(result)
        return result

    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        yield await self.write(document)

    async def write_to_file(self, document: BaseDocument, target: Path, options: dict[str, Any] | None = None) -> None:
        target.write_bytes(await self.write(document))

    def get_supported_media_types(self) -> list[str]:
        return ["application/graphql", "application/json"]

    def get_supported_extensions(self) -> list[str]:
        return [".gql.query"]
