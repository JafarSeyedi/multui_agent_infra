from __future__ import annotations

import hashlib
import math
from typing import Dict, Iterable, List, Sequence

from engines.document.ingestion.ingestion_models import ChunkRecord

from .base import EmbeddingProvider


class HashEmbeddingProvider(EmbeddingProvider):
    """Deterministic fallback embedder for tests and offline development."""

    def __init__(self, dimensions: int = 128) -> None:
        self.dimensions = dimensions

    async def embed_texts(self, texts: Sequence[str]) -> List[List[float]]:
        return [self._embed_single(text) for text in texts]

    def _embed_single(self, text: str) -> List[float]:
        vector = [0.0] * self.dimensions
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]


class DocumentEmbeddingService:
    """Batching helper that generates embeddings for document chunks."""

    def __init__(self, provider: EmbeddingProvider, batch_size: int = 32) -> None:
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        self.provider = provider
        self.batch_size = batch_size

    async def embed_chunks(self, chunks: Sequence[ChunkRecord]) -> Dict[str, List[float]]:
        result: Dict[str, List[float]] = {}
        for batch in self._batched(chunks):
            embeddings = await self.provider.embed_texts([chunk.text for chunk in batch])
            for chunk, embedding in zip(batch, embeddings):
                result[chunk.chunk_id] = embedding
        return result

    def _batched(self, chunks: Sequence[ChunkRecord]) -> Iterable[Sequence[ChunkRecord]]:
        for start in range(0, len(chunks), self.batch_size):
            yield chunks[start : start + self.batch_size]
