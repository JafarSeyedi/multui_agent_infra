from typing import Any

from .base_retriever import BaseRetriever
from .bm25_retriever import BM25KeywordRetriever
from .retriever_result import RetrievalResult
from .vector_retriever import VectorRetriever

class HybridRetriever(BaseRetriever):
    """
    Production-grade hybrid retriever combining:

    - Dense Vector Retrieval (ANN / HNSW / Faiss / Redis)
    - Keyword Retrieval (BM25)
    - RRF Fusion (Reciprocal Rank Fusion)

    Goal:
        سرعت بالا، dedup سریع، scoring استاندارد، و output یکنواخت
    """

    def __init__(
        self,
        vector_retriever: VectorRetriever,
        keyword_retriever: BM25KeywordRetriever,
        k: int = 60,    # RRF constant
    ):
        self.vector_retriever = vector_retriever
        self.keyword_retriever = keyword_retriever
        self.k = k

    # ---------------------------------------------------------
    # Fast RRF Merge
    # ---------------------------------------------------------
    def _rrf_merge(
        self,
        vec_results: list[RetrievalResult],
        kw_results: list[RetrievalResult],
        top_k: int,
    ) -> list[RetrievalResult]:

        scores: dict[str, float] = {}
        chunks: dict[str, RetrievalResult] = {}

        # -----------------------------
        # Vector results
        # -----------------------------
        for rank, r in enumerate(vec_results, start=1):
            cid = r.chunk.chunk_id
            chunks[cid] = r
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (self.k + rank)

        # -----------------------------
        # Keyword results
        # -----------------------------
        for rank, r in enumerate(kw_results, start=1):
            cid = r.chunk.chunk_id
            if cid not in chunks:
                chunks[cid] = r
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (self.k + rank)

        # -----------------------------
        # Convert to list
        # -----------------------------
        merged = [
            RetrievalResult(
                chunk=chunks[cid].chunk,
                score=scores[cid],
                source=chunks[cid].source,
            )
            for cid in scores.keys()
        ]

        # -----------------------------
        # Sort + trim
        # -----------------------------
        merged.sort(key=lambda x: x.score, reverse=True)
        return merged[:top_k]

    # ---------------------------------------------------------
    # Search (Hybrid)
    # ---------------------------------------------------------
    async def search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievalResult]:

        # Parallel retrieval (async)
        vec_task = self.vector_retriever.search(
            query=query,
            top_k=top_k,
            filters=filters,
        )

        kw_task = self.keyword_retriever.search(
            query=query,
            top_k=top_k,
        )

        vec_results, kw_results = await vec_task, await kw_task

        return self._rrf_merge(vec_results, kw_results, top_k)
