"""
Knowledge RAG Engine
====================
Unified RAG engine integrating retrieval, reranking, planning, agentic reasoning,
and graph-enhanced retrieval for the knowledge layer.
"""
from __future__ import annotations

from typing import Any, Optional

from engines.document.models.base import BaseDocument
from engines.document.parsers.base import BaseDocumentParser
from engines.document.writers.base import BaseDocumentWriter, WriteResult

from .retrieval.base_retriever import BaseRetriever
from .retrieval.vector_retriever import VectorRetriever
from .retrieval.hybrid_retriever import HybridRetriever
from .retrieval.bm25_retriever import BM25KeywordRetriever
from .retrieval.keyword_retriever import KeywordRetriever
from .retrieval.retriever_result import RetrievalResult
from .rag_models import RetrievedDocument
from .reranking.reranker import Reranker
from .planner.adaptive_planner import AdaptiveRetrievalPlanner
from .planner.retrieval_plan import RetrievalPlan
from .agentic.retrieval_agent import RetrievalAgent
from .agentic.multihop_reasoner import MultiHopReasoner
from .agentic.query_decomposer import QueryDecomposer
from .agentic.evidence_tracker import EvidenceTracker
from .agentic.uncertainty import UncertaintyEstimator
from .evidence.evidence_clusterer import EvidenceClusterer
from .learning.retrieval_policy import RetrievalPolicy
from .trainer.reranker_trainer import RerankerTrainer
from .trainer.fusion_trainer import FusionTrainer
from .reflection.reflection_loop import ReflectionLoop
from .reflection.reflection_critic import RetrievalCritic
from .vector_service import VectorService
from .embedding import EmbeddingModel
from .chunking import Chunker
from .query_rewriter import QueryRewriter
from .llm_factory import create_llm
from ...storage.vector.base import VectorDBAdapter
from ...document.storage.document_store import DocumentStore


class _StubLLM:
    async def text(self, prompt: str) -> str:
        return ""
    async def json(self, prompt: str) -> list[str]:
        return []
    async def generate(self, prompt: str) -> str:
        return ""


class KnowledgeRagEngine:
    """
    Unified RAG Engine for the Knowledge Layer.
    
    Integrates:
    - Multi-modal retrieval (vector, keyword, BM25, hybrid)
    - Reranking and fusion
    - Adaptive query planning
    - Agentic reasoning (multi-hop, query decomposition)
    - Evidence tracking and clustering
    - Learning-based retrieval optimization
    - Reflection and self-correction
    - Graph-enhanced retrieval (via knowledge graph)
    """
    
    def __init__(self, document_store: DocumentStore, vector_db: VectorDBAdapter, config: dict | None = None) -> None:
        self.config = config or {}
        
        # Core services
        self.llm_factory = create_llm
        self._llm = _StubLLM()
        self.embedding_service = EmbeddingModel()
        self.chunking_service = Chunker()
        self.vector_db=vector_db
        self.document_store=document_store
        self.vector_service = VectorService(
            document_store=document_store,
            vector_db=vector_db,
            embedding_model=self.embedding_service,
            chunker=self.chunking_service,
        )
        self.query_rewriter = QueryRewriter(self._llm)
        
        # Retrieval components
        self._retrievers: dict[str, BaseRetriever] = {}
        self._default_retriever: BaseRetriever | None = None
        
        # Reranking
        self.reranker: Reranker | None = None
        
        # Planning
        self.planner: AdaptiveRetrievalPlanner | None = None
        
        # Agentic reasoning
        self.retrieval_agent: RetrievalAgent | None = None
        self.multihop_reasoner: MultiHopReasoner | None = None
        self.query_decomposer: QueryDecomposer | None = None
        self.evidence_tracker: EvidenceTracker | None = None
        self.uncertainty_estimator: UncertaintyEstimator | None = None
        
        # Evidence processing
        self.evidence_clusterer: EvidenceClusterer | None = None
        
        # Learning
        self.retrieval_policy: RetrievalPolicy | None = None
        
        # Training
        self.reranker_trainer: RerankerTrainer | None = None
        self.fusion_trainer: FusionTrainer | None = None
        
        # Reflection
        self.reflection_loop: ReflectionLoop | None = None
        self.reflection_critic: RetrievalCritic | None = None
        
        # Parsers/Writers for model-driven architecture
        self._parsers: dict[str, BaseDocumentParser] = {}
        self._writers: dict[str, BaseDocumentWriter] = {}
        
        # Initialize default components
        self._initialize_defaults()
    
    def _initialize_defaults(self) -> None:
        """Initialize default retrieval components."""
        # Vector retriever
        vector_retriever = VectorRetriever(
            vector_db=self.vector_db,
            embedding_model=self.embedding_service,
        )
        self.register_retriever("vector", vector_retriever)
        self._default_retriever = vector_retriever
        
        # BM25 retriever
        bm25_retriever = BM25KeywordRetriever(document_store=self.document_store)
        self.register_retriever("bm25", bm25_retriever)
        
        # Keyword retriever
        self.register_retriever("keyword", KeywordRetriever(document_store=self.document_store))
        
        # Hybrid retriever
        self.register_retriever("hybrid", HybridRetriever(vector_retriever=vector_retriever, keyword_retriever=bm25_retriever))
        
        # Reranker
        self.reranker = Reranker()
        
        # Planner
        self.planner = AdaptiveRetrievalPlanner()
        
        # Agentic components
        self.query_decomposer = QueryDecomposer(self._llm)
        self.evidence_tracker = EvidenceTracker()
        self.uncertainty_estimator = UncertaintyEstimator(self._llm)
        self.multihop_reasoner = MultiHopReasoner(self._llm)
        self.retrieval_agent = RetrievalAgent(
            planner=self.planner,
        )
        
        # Evidence clusterer
        self.evidence_clusterer = EvidenceClusterer(embedding_model=self.embedding_service)
        
        # Learning
        self.retrieval_policy = RetrievalPolicy()
        
        # Trainers
        self.reranker_trainer = RerankerTrainer(model=None, optimizer=None)
        self.fusion_trainer = FusionTrainer(fusion_mlp=None, lr=0.001, batch_size=32)
        
        # Reflection
        self.reflection_critic = RetrievalCritic(self._llm)
        self.reflection_loop = ReflectionLoop(
            llm=self._llm,
            critic=self.reflection_critic,
        )
    
    # ============================================================
    # Retrieval Interface
    # ============================================================
    
    def register_retriever(self, name: str, retriever: BaseRetriever) -> None:
        """Register a retriever."""
        self._retrievers[name] = retriever
    
    def get_retriever(self, name: str) -> BaseRetriever | None:
        """Get a registered retriever."""
        return self._retrievers.get(name)
    
    async def retrieve(
        self,
        query: str,
        retriever_name: str | None = None,
        top_k: int = 10,
        **options: Any,
    ) -> list[RetrievalResult]:
        """
        Execute retrieval using specified or default retriever.
        """
        retriever = self._retrievers.get(retriever_name or "vector")
        if retriever is None:
            retriever = self._default_retriever
        if retriever is None:
            raise ValueError("No retriever available")
        
        return await retriever.search(query, top_k=top_k, **options)
    
    async def retrieve_with_rerank(
        self,
        query: str,
        retriever_name: str | None = None,
        top_k: int = 10,
        rerank_top_k: int = 5,
        **options: Any,
    ) -> list[RetrievalResult]:
        """
        Retrieve and rerank results.
        """
        results = await self.retrieve(query, retriever_name, top_k, **options)
        
        if self.reranker and results:
            scores = await self.reranker.rerank(query, [r.chunk for r in results])
            scored = sorted(zip(results, scores), key=lambda x: x[1], reverse=True)
            results = [r for r, _ in scored[:rerank_top_k]]
        
        return results
    
    # ============================================================
    # Agentic Reasoning Interface
    # ============================================================
    
    async def answer_with_agent(
        self,
        query: str,
        max_hops: int = 3,
        **options: Any,
    ) -> dict[str, Any]:
        """
        Answer a query using the agentic retrieval agent.
        """
        if self.retrieval_agent is None:
            raise RuntimeError("Retrieval agent not initialized")
        
        return await self.retrieval_agent.answer(query, max_hops=max_hops, **options)
    
    async def decompose_query(self, query: str) -> list[str]:
        """Decompose a complex query into sub-queries."""
        if self.query_decomposer is None:
            raise RuntimeError("Query decomposer not initialized")
        return await self.query_decomposer.decompose(query)
    
    async def reason_multi_hop(
        self,
        query: str,
        initial_evidence: list[RetrievalResult],
        max_hops: int = 3,
    ) -> dict[str, Any]:
        """Perform multi-hop reasoning."""
        if self.multihop_reasoner is None:
            raise RuntimeError("Multi-hop reasoner not initialized")
        return await self.multihop_reasoner.reason(query, initial_evidence, max_hops)
    
    # ============================================================
    # Planning Interface
    # ============================================================
    
    async def create_retrieval_plan(self, query: str) -> RetrievalPlan:
        """Create an adaptive retrieval plan."""
        if self.planner is None:
            raise RuntimeError("Planner not initialized")
        return await self.planner.plan(query)
    
    # ============================================================
    # Evidence Processing
    # ============================================================
    
    async def cluster_evidence(self, evidence: list[RetrievedDocument]) -> list[RetrievedDocument]:
        """Cluster evidence by topic/similarity."""
        if self.evidence_clusterer is None:
            raise RuntimeError("Evidence clusterer not initialized")
        return await self.evidence_clusterer.cluster(evidence)
    
    # ============================================================
    # Learning & Optimization
    # ============================================================
    
    async def optimize_retrieval(self, query: str, feedback: dict[str, Any]) -> None:
        """Optimize retrieval based on feedback."""
        if self.retrieval_policy:
            await self.retrieval_policy.update(query, feedback)
    
    async def train_reranker(self, training_data: list[dict]) -> None:
        """Train the reranker."""
        if self.reranker_trainer:
            await self.reranker_trainer.train(training_data, epochs=10)

    async def train_fusion(self, training_data: list[dict]) -> None:
        """Train the fusion model."""
        if self.fusion_trainer:
            await self.fusion_trainer.train(training_data, epochs=10)
    
    # ============================================================
    # Reflection & Self-Correction
    # ============================================================
    
    async def reflect_and_improve(
        self,
        query: str,
        initial_answer: str,
        evidence: list[RetrievalResult],
    ) -> str:
        """Use reflection to improve answer quality."""
        if self.reflection_loop:
            return await self.reflection_loop.run(query, initial_answer, evidence)  # type: ignore[arg-type]
        return initial_answer
    
    # ============================================================
    # Model-Driven Architecture (Parsers/Writers)
    # ============================================================
    
    def register_parser(self, fmt: str, parser: BaseDocumentParser) -> None:
        """Register a parser for model-driven parsing."""
        self._parsers[fmt] = parser
    
    def register_writer(self, fmt: str, writer: BaseDocumentWriter) -> None:
        """Register a writer for model-driven writing."""
        self._writers[fmt] = writer
    
    async def parse(self, source: str, fmt: str | None = None, **options: Any) -> BaseDocument:
        """Parse using model-driven parser."""
        parser = self._parsers.get(fmt or "default")
        if parser is None:
            raise LookupError(f"No parser registered for format '{fmt}'")
        import engines.document.parsers.base as parser_base
        result = await parser.parse_bytes(source.encode() if isinstance(source, str) else source, document_id="", source_name=source if isinstance(source, str) else str(source))
        return result
    
    async def write(self, document: BaseDocument, destination: str, fmt: str | None = None, **options: Any) -> WriteResult:
        """Write using model-driven writer."""
        writer = self._writers.get(fmt or "default")
        if writer is None:
            raise LookupError(f"No writer registered for format '{fmt}'")
        data = await writer.write(document)
        result = WriteResult(metadata={"destination": destination, "format": fmt, "data": data})
        return result
    
    # ============================================================
    # Graph-Enhanced Retrieval (Integration with Knowledge Graph)
    # ============================================================
    
    async def retrieve_with_graph(
        self,
        query: str,
        graph_engine: Any,  # UnifiedGraphEngine or SemanticGraphEngine
        top_k: int = 10,
        **options: Any,
    ) -> list[RetrievalResult]:
        """
        Enhance retrieval with knowledge graph context.
        """
        # Get graph-relevant entities
        graph_results = await graph_engine.search(query, top_k=top_k)
        
        # Combine with vector retrieval
        vector_results = await self.retrieve(query, top_k=top_k)
        
        # Merge and deduplicate
        combined = self._merge_results(vector_results, graph_results)
        
        # Rerank
        if self.reranker:
            scores = await self.reranker.rerank(query, [r.chunk for r in combined])
            scored = sorted(zip(combined, scores), key=lambda x: x[1], reverse=True)
            combined = [r for r, _ in scored]
        
        return combined[:top_k]
    
    def _merge_results(
        self,
        vector_results: list[RetrievalResult],
        graph_results: list[Any],
    ) -> list[RetrievalResult]:
        """Merge vector and graph results."""
        # Simple merge - in practice, use more sophisticated fusion
        seen = set()
        merged = []
        
        for r in vector_results + graph_results:
            key = getattr(r, "id", getattr(r, "content", str(r)))
            if key not in seen:
                seen.add(key)
                merged.append(r)
        
        return merged


# Backward compatibility
RAG_Engine = KnowledgeRagEngine