from typing import List
from config.models.rag.rag_models import DocumentChunk


class BaseCompressor:

    async def compress(
        self,
        query: str,
        chunks: List[DocumentChunk]
    ) -> List[DocumentChunk]:
        raise NotImplementedError
