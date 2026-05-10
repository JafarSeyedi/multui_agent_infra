from __future__ import annotations

import asyncio
from collections.abc import Callable
from statistics import mean
from typing import Any

from .base_retriever import BaseRetriever
from .bm25_retriever import BM25KeywordRetriever
from .retriever_result import RetrievalResult
from .vector_retriever import VectorRetriever
from engines.rag.llm.llm_protocols import AsyncLLM

class HybridRetrieverPlus(BaseRetriever):
    """Hybrid retriever with query analysis, adaptive fusion, and score boosting."""

    def __init__(
        self,
        vector_retriever: VectorRetriever,
        keyword_retriever: BM25KeywordRetriever,
        llm: AsyncLLM | None = None,
        chunk_frequency_getter: Callable[[str], float] | None = None,
        base_k: int = 60,
    ):
        self.vector_retriever = vector_retriever
        self.keyword_retriever = keyword_retriever
        self.llm = llm
        self.get_frequency = chunk_frequency_getter
        self.base_k = base_k

    def _analyze_query(self, query: str) -> dict[str, Any]:
        tokens = [token for token in query.split() if token]
        return {
            "length": len(tokens),
            "entity_query": any(token[:1].isupper() for token in tokens),
            "numeric_query": any(char.isdigit() for char in query),
            "complex_long": len(tokens) > 12,
            "short_keyword_like": len(tokens) <= 4,
        }

    async def _semantic_keywords(self, query: str) -> list[str]:
        if not self.llm:
            return []

        prompt = (
            "Extract 4-8 compact retrieval keywords for this query. "
            "Return only a comma-separated list.\n"
            f"Query: {query}"
        )
        try:
            response = await self.llm.ainvoke(prompt)
        except Exception:
            return []
        return [word.strip().lower() for word in str(response).split(",") if word.strip()]

    async def _dynamic_rrf_from_llm(self, query: str) -> int:
        if not self.llm:
            return self.base_k
        prompt = (
            "Choose an integer reciprocal-rank-fusion constant between 10 and 200. "
            "Return only the integer.\n"
            f"Query: {query}"
        )
        try:
            response = await self.llm.ainvoke(prompt)
            return max(10, min(200, int(str(response).strip())))
        except Exception:
            return self.base_k

    def _normalize_scores(self, results: list[RetrievalResult]) -> list[RetrievalResult]:
        if not results:
            return results
        scores = [result.score for result in results]
        avg = mean(scores)
        high = max(scores)
        low = min(scores)
        scale = (high - low) or 1.0
        for result in results:
            centered = (result.score - avg) / scale
            result.score = max(0.0, min(1.0, 0.5 + 0.5 * centered))
        return results

    def _cross_filter(
        self,
        vector_results: list[RetrievalResult],
        keyword_results: list[RetrievalResult],
    ) -> list[RetrievalResult]:
        keyword_ids = {result.chunk.chunk_id for result in keyword_results}
        for result in vector_results:
            if result.chunk.chunk_id in keyword_ids:
                result.score *= 1.2
        return vector_results

    def _frequency_boost(self, result: RetrievalResult) -> None:
        if not self.get_frequency:
            return
        frequency = self.get_frequency(result.chunk.chunk_id) or 0.0
        if frequency > 0:
            result.score *= 1.0 + min(0.4, float(frequency))

    def _merge(
        self,
        vec_results: list[RetrievalResult],
        kw_results: list[RetrievalResult],
        top_k: int,
        k_rrf: int,
        analysis: dict[str, Any],
    ) -> list[RetrievalResult]:
        scores: dict[str, float] = {}
        chunks: dict[str, RetrievalResult] = {}

        vec_weight = 1.3 if analysis["complex_long"] else 1.0
        kw_weight = 1.35 if analysis["short_keyword_like"] else 1.0

        for rank, result in enumerate(vec_results, start=1):
            chunk_id = result.chunk.chunk_id
            chunks[chunk_id] = result
            scores[chunk_id] = scores.get(chunk_id, 0.0) + vec_weight * (1.0 / (k_rrf + rank))

        for rank, result in enumerate(kw_results, start=1):
            chunk_id = result.chunk.chunk_id
            chunks.setdefault(chunk_id, result)
            scores[chunk_id] = scores.get(chunk_id, 0.0) + kw_weight * (1.0 / (k_rrf + rank))

        merged: list[RetrievalResult] = []
        for chunk_id, score in scores.items():
            result = RetrievalResult(
                chunk=chunks[chunk_id].chunk,
                score=score,
                source=chunks[chunk_id].source,
                meta=dict(chunks[chunk_id].meta),
            )
            self._frequency_boost(result)
            merged.append(result)

        merged.sort(key=lambda item: item.score, reverse=True)
        return merged[:top_k]

    async def search(
        self,
        query: str,
        top_k: int = 8,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievalResult]:
        analysis = self._analyze_query(query)
        keywords = await self._semantic_keywords(query)
        expanded_query = query if not keywords else f"{query} {' '.join(keywords)}"
        k_rrf = await self._dynamic_rrf_from_llm(query)

        vector_results, keyword_results = await asyncio.gather(
            self.vector_retriever.search(query=expanded_query, top_k=top_k, filters=filters),
            self.keyword_retriever.search(query=expanded_query, top_k=top_k),
        )

        vector_results = self._cross_filter(self._normalize_scores(vector_results), keyword_results)
        keyword_results = self._normalize_scores(keyword_results)
        return self._merge(vector_results, keyword_results, top_k=top_k, k_rrf=k_rrf, analysis=analysis)
