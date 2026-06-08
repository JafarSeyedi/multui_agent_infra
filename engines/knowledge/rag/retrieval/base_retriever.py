# rag/retrieval/base_retriever.py
from abc import ABC
from abc import abstractmethod

from engines.knowledge.rag.retrieval.retriever_result import RetrievalResult

class BaseRetriever(ABC):
    """Common contract for all Retrievers"""

    @abstractmethod
    async def search(self, query: str, top_k: int = 10) -> list[RetrievalResult]:
        """Search and return Results"""
        ...
