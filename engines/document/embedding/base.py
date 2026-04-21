from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Sequence


class EmbeddingProvider(ABC):
    """Provider interface for generating vector embeddings for document text."""
    name: str
    @abstractmethod
    async def embed_texts(self, texts: Sequence[str]) -> List[List[float]]:
        ...

    async def embed_query(self, text: str) -> List[float]:
        embeddings = await self.embed_texts([text])
        return embeddings[0]
