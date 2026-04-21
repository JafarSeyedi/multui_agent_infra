# engines/document/ingestion/steps/step_embed.py

from __future__ import annotations
from datetime import datetime
from typing import List
from engines.document.ingestion.ingestion_models import EmbeddingRecord
from engines.document.ingestion.ingestion_context import IngestionContext
from engines.document.ingestion.ingestion_errors import EmbeddingFailed


async def step_embed(ctx: IngestionContext) -> IngestionContext:
    """
    Step 4 — Embed:
        - Use EmbeddingProvider to compute embeddings for each chunk
        - Store vectors inside ChunkRecord objects
    """
    if not ctx.chunks:
        return ctx

    if ctx.embedding_service is None:
        return ctx  # embedding disabled

    try:
        # embed_chunks returns: Dict[chunk_id -> embedding]
        embed_map = await ctx.embedding_service.embed_chunks(ctx.chunks)

        all_embeddings: List[EmbeddingRecord] = []

        for chunk in ctx.chunks:
            emb_vector = embed_map.get(chunk.chunk_id)
            if emb_vector is None:
                continue  # یا raise EmbeddingFailed

            emb_record = EmbeddingRecord(
                document_id=chunk.document_id,
                chunk_id=chunk.chunk_id,
                vector=emb_vector,
                dim=len(emb_vector),
                provider=ctx.embedding_service.provider.name,
                created_at=datetime.utcnow(),
            )

            chunk.embeddings.append(emb_record)
            all_embeddings.append(emb_record)

        ctx.embeddings = all_embeddings
        return ctx

    except Exception as exc:
        raise EmbeddingFailed(f"Failed to compute embeddings: {exc}") from exc
