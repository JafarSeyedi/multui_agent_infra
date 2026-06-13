from abc import ABC, abstractmethod

from ..rag_models import DocumentChunk


class BaseCompressor(ABC):

    @abstractmethod
    async def compress(
        self,
        query: str,
        chunks: list[DocumentChunk]
    ) -> list[DocumentChunk]:
        ...
