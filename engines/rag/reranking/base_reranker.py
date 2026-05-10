# storage/vector/base_reranker.py
from abc import ABC
from abc import abstractmethod
from collections.abc import Sequence

from engines.rag.rag_models import DocumentChunk

class BaseReranker(ABC):
    """قرارداد مشترک تمام Reranker ها"""

    @abstractmethod
    async def rerank(self, query: str, chunks: Sequence[DocumentChunk]) -> list[float]:
        """مرتب‌سازی مجدد نتایج بر اساس relevance"""
