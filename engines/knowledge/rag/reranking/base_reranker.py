# storage/vector/base_reranker.py
from abc import ABC
from abc import abstractmethod
from collections.abc import Sequence

from engines.knowledge.rag.rag_models import DocumentChunk

class BaseReranker(ABC):
    """Common contract for all Rerankers"""

    @abstractmethod
    async def rerank(self, query: str, chunks: Sequence[DocumentChunk]) -> list[float]:
        """Re-rank Results based on relevance"""
