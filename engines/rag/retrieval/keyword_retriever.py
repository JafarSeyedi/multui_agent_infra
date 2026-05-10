from ...document.storage.document_store import DocumentStore
from .base_retriever import BaseRetriever
from .retriever_result import RetrievalResult

# ---------------------------------------------------------
# Keyword Retriever (Simple BM25-style scoring)
# ---------------------------------------------------------

class KeywordRetriever(BaseRetriever):

    def __init__(self, document_store: DocumentStore):
        self.document_store = document_store

    async def search(self, query: str, top_k: int = 5) -> list[RetrievalResult]:

        tokens = query.lower().split()

        scores = []

        for chunk in self.document_store.chunks.values():

            text = chunk.text.lower()

            score = 0

            for token in tokens:
                if token in text:
                    score += 1

            if score > 0:
                scores.append(RetrievalResult(chunk, score,source="keyword"))

        scores.sort(key=lambda x: x.score, reverse=True)

        return scores[:top_k]
