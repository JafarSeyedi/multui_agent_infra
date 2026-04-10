from typing import List
from rag.rag_models import DocumentChunk


class BaseCompressor:

    async def compress(
        self,
        query: str,
        chunks: List[DocumentChunk]
    ) -> List[DocumentChunk]:
        raise NotImplementedError
