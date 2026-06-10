from __future__ import annotations

import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, BinaryIO, TextIO, cast

from engines.document.models.query_models import UnifiedQueryDocument, DaxQuery, RestTransport, QueryTransport
from engines.document.writers.base import BaseDocument, BaseDocumentWriter


class DaxWriter(BaseDocumentWriter):
    supported_format = None

    def can_write(self, document) -> bool:
        return isinstance(document, UnifiedQueryDocument) and document.dax is not None

    async def write(self, document: BaseDocument, destination: str | Path | BinaryIO | TextIO | None = None, **options: Any) -> bytes:
        doc = cast(UnifiedQueryDocument, document)
        dax = doc.dax or DaxQuery()

        if doc.transport == QueryTransport.REST_JSON:
            payload: dict[str, Any] = {
                "queries": [{"Expression": dax.expression}],
            }
            if doc.rest_transport:
                payload["endpoint"] = doc.rest_transport.endpoint
            result = json.dumps(payload, indent=2).encode("utf-8")
        else:
            text = dax.expression
            if dax.variables:
                var_block = "\n".join(f"VAR {k} = {v}" for k, v in dax.variables.items())
                text = f"{var_block}\nRETURN\n{dax.expression}"
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
        return ["text/plain", "application/json"]

    def get_supported_extensions(self) -> list[str]:
        return [".dax", ".dax.json"]
