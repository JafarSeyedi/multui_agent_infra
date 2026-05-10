from engines.rag.rag_models import DocumentChunk


class BaseCompressor:

    async def compress(
        self,
        query: str,
        chunks: list[DocumentChunk]
    ) -> list[DocumentChunk]:
        raise NotImplementedError
