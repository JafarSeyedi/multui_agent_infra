# engines/document/ingestion/steps/step_extract.py

from __future__ import annotations
from typing import Optional
from engines.document.ingestion.ingestion_context import IngestionContext
from engines.document.ingestion.ingestion_errors import ExtractionFailed


async def step_extract(ctx: IngestionContext) -> IngestionContext:
    """
    Step 1 — Extract:
        - Build AssetRecord (metadata only)
        - Upload bytes to object storage (if enabled)
        - Save asset info into ctx.asset
        NOTE: DocumentStore does NOT handle assets.
              Actual document persistence happens later in step_store.
    """
    if ctx.document_store is None:
        raise ExtractionFailed("document_store is not configured")

    try:
        asset = ctx.build_asset_record()

        ctx.object_key = f"{ctx.document_id}/raw"
        # Store binary data in object storage
        if ctx.object_storage is not None:
            await ctx.object_storage.put(
                ctx.object_key,
                data=ctx.data,
            )
        asset.object_key = ctx.object_key

        # Save asset into the context (NOT document store)
        ctx.asset = asset

    except Exception as exc:
        raise ExtractionFailed(f"Failed to extract document: {exc}") from exc
    return ctx
