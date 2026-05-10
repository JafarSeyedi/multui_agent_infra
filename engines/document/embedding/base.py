from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from collections.abc import Sequence


class EmbeddingProvider(ABC):
    """Provider interface for generating vector embeddings for document text."""
    name: str
    @abstractmethod
    async def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        ...

    async def embed_query(self, text: str) -> list[float]:
        embeddings = await self.embed_texts([text])
        return embeddings[0]
