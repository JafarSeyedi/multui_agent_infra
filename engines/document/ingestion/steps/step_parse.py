# engines/document/ingestion/steps/step_parse.py
from __future__ import annotations

from ...models.base import BaseDocument
from ...models.document_registry import DocumentRegistry
from ..ingestion_context import IngestionContext
from ..ingestion_errors import ParseFailed
from ..ingestion_errors import UnsupportedMediaTypeError

async def step_parse(ctx: IngestionContext) -> IngestionContext:
    """
    Step 2 — Parse:
        - Determine parser from registry by extension/media type
        - Convert raw bytes → BaseDocument
    """
    try:
        registry = DocumentRegistry()
        parser = registry.get_parser(ctx.filename)
        if parser is None:
            raise UnsupportedMediaTypeError(ctx.media_type.mime)

        parsed: BaseDocument = await parser.parse_bytes(
            source_name=ctx.filename,
            document_id=ctx.document_id,
            data=ctx.data,
            metadata=ctx.request_metadata,
        )

        ctx.parsed_document = parsed
        return ctx

    except Exception as exc:
        raise ParseFailed(f"Failed to parse document: {exc}") from exc
