# rag/retrieval/base_retriever.py
from abc import ABC
from abc import abstractmethod

from engines.rag.retrieval.retriever_result import RetrievalResult

class BaseRetriever(ABC):
    """قرارداد مشترک تمام Retriever ها"""

    @abstractmethod
    async def search(self, query: str, top_k: int = 10) -> list[RetrievalResult]:
        """جستجو و برگرداندن نتایج"""
        ...
