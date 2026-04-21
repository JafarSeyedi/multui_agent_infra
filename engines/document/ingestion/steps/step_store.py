from __future__ import annotations

from engines.document.ingestion.ingestion_context import IngestionContext
from engines.document.ingestion.ingestion_errors import StorageFailed


async def step_store(ctx: IngestionContext) -> IngestionContext:
    """
    Step 5 — Store:
        - Persist DocumentRecord
        - Persist parsed chunks
        - Persist generated embeddings
    """

    if ctx.document_store is None:
        raise RuntimeError("document_store is required in step_store")

    if ctx.chunk_store is None:
        raise RuntimeError("chunk_store is required in step_store")

    try:
        # --------------------------------------------------------
        # 1. Build DocumentRecord
        # --------------------------------------------------------
        doc = ctx.build_document_record()

        # Inject asset metadata (DocumentRecord has NO asset_key field!)
        if ctx.asset is not None:
            doc.metadata["asset_key"] = ctx.asset.object_key
            doc.metadata["media_type"] = ctx.asset.media_type

        # --------------------------------------------------------
        # 2. Store document record
        # --------------------------------------------------------
        await ctx.document_store.add_document(doc)

        # --------------------------------------------------------
        # 3. Store chunks
        # --------------------------------------------------------
        if ctx.chunks:
            await ctx.chunk_store.add_chunks(ctx.chunks)

    except Exception as exc:
        raise StorageFailed(f"Failed to store records: {exc}") from exc

    return ctx
