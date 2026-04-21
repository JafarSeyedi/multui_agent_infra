# storage/vector/base_reranker.py
from abc import ABC, abstractmethod
from engines.rag.rag_models import DocumentChunk
from typing import Sequence, List

class BaseReranker(ABC):
    """قرارداد مشترک تمام Reranker ها"""

    @abstractmethod
    async def rerank(self, query: str, chunks: Sequence[DocumentChunk]) -> List[float]:
        """مرتب‌سازی مجدد نتایج بر اساس relevance"""
