# engines/document/ingestion/steps/step_chunk.py

from __future__ import annotations

from engines.document.ingestion.ingestion_context import IngestionContext
from engines.document.ingestion.ingestion_errors import ChunkingFailed

async def step_chunk(ctx: IngestionContext) -> IngestionContext:
    """
    Step 3 — Chunk:
        - Use BaseChunker to chunk parsed document
        - Produce list of ChunkRecord items
    """
    if ctx.parsed_document is None:
        raise ChunkingFailed("Cannot chunk before parsing")

    if ctx.chunker is None:
        raise ChunkingFailed("No chunker configured")

    try:
        chunks = await ctx.chunker.chunk_document(
            document=ctx.parsed_document,
            config=ctx.chunking,
        )

        ctx.chunks = chunks
        return ctx

    except Exception as exc:
        raise ChunkingFailed(f"Failed to chunk document: {exc}") from exc
