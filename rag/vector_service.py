from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from config.models.rag.rag_models import Document, DocumentChunk
from rag.services.chunking import Chunker
from rag.services.embedding import EmbeddingModel
from rag.graph.graph_retriever import GraphRetriever
from rag.planner.adaptive_planner import AdaptiveRetrievalPlanner
from rag.services.query_rewriter import QueryRewriter
from rag.reranking import Reranker
from rag.retrieval.bm25_retriever import BM25KeywordRetriever
from rag.retrieval.retrieval_feedback_buffer import RetrievalFeedbackBuffer
from rag.trainer.fusion_trainer import FusionTrainer
from rag.retrieval.hybrid_retriever_super import HybridRetrieverSuper
from rag.retrieval.topk_optimizer import TopKOptimizer
from rag.retrieval.vector_retriever import VectorRetriever
from rag.retrieval.weight_manager import WeightManager
from storage.document_store import DocumentStore
from storage.vector.base import VectorDBAdapter


class QueryResult(BaseModel):
    chunk: DocumentChunk
    score: float
    source: str = "vector"
    rerank_score: Optional[float] = None


class VectorService:
    def __init__(
        self,
        document_store: DocumentStore,
        vector_db: VectorDBAdapter,
        embedding_model: EmbeddingModel,
        chunker: Chunker,
        llm: Optional[Any] = None,
        query_rewriter: Optional[QueryRewriter] = None,
        reranker: Optional[Reranker] = None,
    ):
        self.document_store = document_store
        self.vector_db = vector_db
        self.embedding_model = embedding_model
        self.chunker = chunker
        self.llm = llm
        self.query_rewriter = query_rewriter
        self.reranker = reranker

        self.compressor = None
        self.planner: Optional[AdaptiveRetrievalPlanner] = None
        self.reflection_loop = None
        self.graph_retriever: Optional[GraphRetriever] = None
        self.topk_optimizer = TopKOptimizer()
        self.weight_manager = WeightManager()
        self.feedback_buffer = RetrievalFeedbackBuffer(capacity=5000)
        self.fusion_trainer = FusionTrainer(fusion_mlp=None, lr=1e-4, batch_size=32)
        self._retriever: Optional[HybridRetrieverSuper] = None

    @property
    def retriever(self) -> HybridRetrieverSuper:
        if self._retriever is None:
            vector = VectorRetriever(vector_db=self.vector_db, embedding_model=self.embedding_model)
            keyword = BM25KeywordRetriever(document_store=self.document_store)
            self._retriever = HybridRetrieverSuper(
                vector_retriever=vector,
                keyword_retriever=keyword,
                graph_retriever=self.graph_retriever,
                reranker=self.reranker,
                llm=self.llm,
            )
            self._retriever.attach_feedback_buffer(self.feedback_buffer)
            self.fusion_trainer.fusion_mlp = self._retriever.fusion_mlp
            self.fusion_trainer.ensure_optimizer()
            self._retriever.attach_trainer(self.fusion_trainer)
        return self._retriever

    async def register_feedback(
        self,
        query: str,
        evidences,
        results: List[QueryResult],
        chosen_chunk_id: str,
        positive_chunks, negative_chunks
    ) -> None:
        await self.retriever.collect_feedback(query=query, results=results, chosen_chunk_id=chosen_chunk_id, positive_chunks=positive_chunks, negative_chunks=negative_chunks)
        if len(self.feedback_buffer) > 200:
            await self.retriever.train_from_feedback(batch_size=200)

    async def raw_retrieve(
        self,
        query: str,
        top_k: int,
        filters: Optional[Dict[str, Any]],
    ):
        return await self.retriever.search(query=query, top_k=top_k, filters=filters)

    async def _retrieve_one(self, query: str, top_k: int, filters: Optional[Dict[str, Any]]):
        return await self.retriever.search(query=query, top_k=top_k, filters=filters)

    async def query(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[QueryResult]:
        plan = await self.planner.plan(query) if self.planner else None
        if plan is not None:
            top_k = plan.top_k
        else:
            top_k = self.topk_optimizer.choose(query)

        queries = [query]
        if self.query_rewriter and plan and plan.num_queries > 1:
            rewritten = await self.query_rewriter.rewrite(query, num_queries=plan.num_queries)
            queries = list(dict.fromkeys(rewritten))

        results_lists = await asyncio.gather(
            *(self._retrieve_one(item, top_k, filters) for item in queries)
        )
        merged: Dict[str, QueryResult] = {}
        for result in [item for group in results_lists for item in group]:
            chunk_id = result.chunk.chunk_id
            weighted_score = result.score * self.weight_manager.get(result.source)
            existing = merged.get(chunk_id)
            if existing is None or weighted_score > existing.score:
                merged[chunk_id] = QueryResult(chunk=result.chunk, score=weighted_score, source=result.source)

        results = list(merged.values())
        if self.graph_retriever:
            results = await self._graph_expand(results)

        results.sort(key=lambda item: item.score, reverse=True)
        results = results[:top_k]

        if self.compressor and plan and plan.compression != "none":
            compressed_chunks = await self.compressor.compress(query=query, chunks=[result.chunk for result in results])
            for result, compressed_chunk in zip(results, compressed_chunks):
                result.chunk = compressed_chunk

        if self.reranker and (plan is None or plan.use_rerank):
            rerank_scores = await self.reranker.rerank(query=query, chunks=[result.chunk for result in results])
            for result, rerank_score in zip(results, rerank_scores):
                result.rerank_score = rerank_score
                result.score = 0.7 * result.score + 0.3 * rerank_score
            results.sort(key=lambda item: item.score, reverse=True)

        return results

    async def _graph_expand(self, results: List[QueryResult], hops: int = 1) -> List[QueryResult]:
        if not self.graph_retriever:
            return results

        expanded = {result.chunk.chunk_id: result for result in results}
        for result in results:
            entity = (result.chunk.metadata or {}).get("entity")
            if not entity:
                continue
            neighbors = await self.graph_retriever.retrieve(entity_id=entity, hops=hops)
            for node in neighbors:
                chunk = await self.document_store.get_chunk(node.id)
                if chunk and chunk.chunk_id not in expanded:
                    expanded[chunk.chunk_id] = QueryResult(
                        chunk=chunk,
                        score=result.score * 0.85 * self.weight_manager.get("graph"),
                        source="graph",
                    )
        return list(expanded.values())

    async def add_document(
        self,
        document: Document,
        auto_chunk: bool = True,
        store_chunks: bool = True,
    ) -> List[DocumentChunk]:
        await self.document_store.add_document(document)
        chunks = await self.chunker.create_chunks(document) if auto_chunk else []
        if store_chunks and chunks:
            await self.document_store.add_chunks(chunks)
            if self._retriever is not None:
                self._retriever.keyword_retriever.invalidate()

        if not chunks:
            return []

        embeddings = await self.embedding_model.embed([chunk.text for chunk in chunks])
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding

        await self.vector_db.add_embeddings(
            ids=[chunk.chunk_id for chunk in chunks],
            embeddings=embeddings,
            metadata=[chunk.dict() for chunk in chunks],
        )
        return chunks

    async def delete_document(self, document_id: str) -> None:
        chunks = await self.document_store.get_chunks_by_doc(document_id)
        chunk_ids = [chunk.chunk_id for chunk in chunks]
        if chunk_ids:
            await self.vector_db.delete_embeddings(chunk_ids)
        await self.document_store.delete_document(document_id)
        if self._retriever is not None:
            self._retriever.keyword_retriever.invalidate()
