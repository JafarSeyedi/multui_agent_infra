from __future__ import annotations

import asyncio
import math
from typing import Any, Dict, List, Optional

from rag.graph.graph_retriever import GraphRetriever
from rag.research.memory.reasoning.event_types import ReasoningEventType
from rag.research.memory.reasoning_memory import ReasoningMemory

from .bm25_retriever import BM25KeywordRetriever
from .retriever_result import RetrievalResult
from .vector_retriever import VectorRetriever
from .base_retriever import BaseRetriever

class FusionMLP:
    """Small dependency-free fusion model with trainable linear weights."""

    def __init__(self, input_dim: int = 3):
        self.weights = [1.0 / input_dim] * input_dim
        self.bias = 0.0

    def predict(self, features: List[float]) -> float:
        total = sum(weight * value for weight, value in zip(self.weights, features)) + self.bias
        return 1.0 / (1.0 + math.exp(-total))

    __call__ = predict


class HybridRetrieverSuper(BaseRetriever):
    """Professional hybrid retrieval pipeline with optional graph and rerank fusion."""

    def __init__(
        self,
        vector_retriever: VectorRetriever,
        keyword_retriever: BM25KeywordRetriever,
        graph_retriever: Optional[GraphRetriever] = None,
        reranker: Optional[Any] = None,
        llm: Optional[Any] = None,
        reasoning: Optional[ReasoningMemory] = None,
    ):
        self.vector_retriever = vector_retriever
        self.keyword_retriever = keyword_retriever
        self.graph_retriever = graph_retriever
        self.reranker = reranker
        self.llm = llm
        self.reasoning = reasoning or ReasoningMemory()
        self.fusion_mlp = FusionMLP()
        self.feedback_buffer = None
        self.trainer = None

    def attach_feedback_buffer(self, buffer) -> None:
        self.feedback_buffer = buffer

    def attach_trainer(self, trainer) -> None:
        self.trainer = trainer

    async def collect_feedback(self, query, results, chosen_chunk_id, positive_chunks, negative_chunks):
        if self.feedback_buffer is None:
            return
        for result in results:
            meta = result.meta or {}
            self.feedback_buffer.add(
                meta.get("vector_raw_score", 0.0),
                meta.get("keyword_raw_score", 0.0),
                meta.get("graph_raw_score", 0.0),
                1.0 if result.chunk.chunk_id == chosen_chunk_id else 0.0,
                positive_chunks, negative_chunks
            )

    async def train_from_feedback(self, batch_size: int = 200):
        if self.trainer is None or self.feedback_buffer is None:
            return None
        samples = self.feedback_buffer.sample(batch_size)
        if not samples:
            return None
        return self.trainer.train(samples, epochs=2)

    def _normalize(self, results: List[RetrievalResult]) -> List[RetrievalResult]:
        if not results:
            return results
        scores = [result.score for result in results]
        mean = sum(scores) / len(scores)
        variance = sum((score - mean) ** 2 for score in scores) / len(scores)
        std = math.sqrt(variance) or 1.0
        for result in results:
            normalized = 0.5 + (0.2 * ((result.score - mean) / std))
            result.score = min(1.0, max(0.0, normalized))
        return results

    def _softmax_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        exps = {key: math.exp(value) for key, value in weights.items()}
        total = sum(exps.values()) or 1.0
        return {key: value / total for key, value in exps.items()}

    def _graph_boost(self, results: List[RetrievalResult], graph_hits: Dict[str, float]) -> List[RetrievalResult]:
        for result in results:
            graph_strength = graph_hits.get(result.chunk.chunk_id)
            if graph_strength is not None:
                result.score *= 1.1 + (0.2 * graph_strength)
                result.meta["graph_raw_score"] = graph_strength
        return results

    async def _fusion_weights_from_llm(self, query: str) -> Dict[str, float]:
        if not self.llm:
            return {"vector": 0.45, "keyword": 0.35, "graph": 0.20}
        prompt = (
            "For the given search query, return JSON with weights for vector, keyword, graph. "
            "Values must sum to 1.0.\n"
            f"Query: {query}"
        )
        try:
            import json

            response = await self.llm.ainvoke(prompt)
            weights = json.loads(response)
            return {key: float(value) for key, value in weights.items()}
        except Exception:
            return {"vector": 0.5, "keyword": 0.3, "graph": 0.2}

    async def search(
        self,
        query: str,
        top_k: int = 8,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievalResult]:
        graph_task = self.graph_retriever.search(query=query, top_k=top_k) if self.graph_retriever else None
        vector_results, keyword_results, graph_results = await asyncio.gather(
            self.vector_retriever.search(query=query, top_k=top_k, filters=filters),
            self.keyword_retriever.search(query=query, top_k=top_k),
            graph_task if graph_task is not None else asyncio.sleep(0, result=[]),
        )

        vector_results = self._normalize(vector_results)
        keyword_results = self._normalize(keyword_results)
        graph_results = self._normalize(graph_results)
        fusion_weights = self._softmax_weights(await self._fusion_weights_from_llm(query))

        all_chunks: Dict[str, Dict[str, Any]] = {}
        streams = {
            "vector": (vector_results, fusion_weights.get("vector", 0.33)),
            "keyword": (keyword_results, fusion_weights.get("keyword", 0.33)),
            "graph": (graph_results, fusion_weights.get("graph", 0.33)),
        }
        for source, (results, weight) in streams.items():
            for rank, result in enumerate(results, start=1):
                bucket = all_chunks.setdefault(
                    result.chunk.chunk_id,
                    {"chunk": result.chunk, "scores": {}, "meta": {}},
                )
                bucket["scores"][source] = weight * (result.score / (rank + 1))
                bucket["meta"].update(result.meta)

        self.reasoning.log(ReasoningEventType.RETRIEVAL_VECTOR, "Vector search executed", meta={"results": len(vector_results)})
        self.reasoning.log(ReasoningEventType.RETRIEVAL_KEYWORD, "Keyword search executed", meta={"results": len(keyword_results)})
        if graph_results:
            self.reasoning.log(ReasoningEventType.RETRIEVAL_GRAPH, "Graph search executed", meta={"results": len(graph_results)})

        merged: List[RetrievalResult] = []
        for bundle in all_chunks.values():
            features = [
                bundle["scores"].get("vector", 0.0),
                bundle["scores"].get("keyword", 0.0),
                bundle["scores"].get("graph", 0.0),
            ]
            score = self.fusion_mlp.predict(features)
            merged.append(
                RetrievalResult(
                    chunk=bundle["chunk"],
                    score=score,
                    source="fusion",
                    meta=bundle["meta"],
                )
            )

        if self.graph_retriever and getattr(self.graph_retriever, "link_strengths", None):
            merged = self._graph_boost(merged, self.graph_retriever.link_strengths)

        if self.reranker:
            rerank_scores = await self.reranker.rerank(query, [result.chunk for result in merged])
            for result, rerank_score in zip(merged, rerank_scores):
                result.meta["rerank_score"] = rerank_score
                result.score = 0.7 * result.score + 0.3 * float(rerank_score)

        merged.sort(key=lambda result: result.score, reverse=True)
        return merged[:top_k]
