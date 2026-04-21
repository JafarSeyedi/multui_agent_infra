from __future__ import annotations

import time
from typing import Any, List, Optional

from engines.rag.research.citation_manager import CitationManager
from engines.rag.research.evaluation.evaluation_controller import EvaluationController
from engines.rag.research.evaluation.improvement_engine import ImprovementEngine
from engines.rag.research.evaluation.schema import Evidence, ResearchAnswer
from engines.rag.research.graph.entity_extractor import EntityExtractor
from engines.rag.research.graph.graph_index import GraphIndex
from engines.rag.research.graph.graph_traverser import GraphTraverser
from engines.rag.research.graph.relation_builder import RelationBuilder
from engines.rag.research.guardrails.hallucination_guard import HallucinationGuard
from engines.rag.research.improvement.feedback_controller import FeedbackController
from engines.rag.research.memory.memory_controller import MemoryController
from engines.rag.research.memory.reasoning.event_types import ReasoningEventType
from engines.rag.research.memory.reasoning_memory import ReasoningMemory
from engines.rag.research.observability.observability_controller import ObservabilityController
from engines.rag.research.summarization.research_summarizer import ResearchSummarizer
from engines.rag.research.base_research_agent import BaseResearchAgent

class ResearchAgent(BaseResearchAgent):
    def __init__(
        self,
        planner,
        citation_manager: CitationManager,
        research_loop,
        entity_extractor: EntityExtractor,
        relation_builder: RelationBuilder,
        relation_ranker,
        canonicalizer,
        graph_index: GraphIndex,
        graph_persistence,
        graph_traverser: GraphTraverser,
        memory_controller: MemoryController,
        llm,
        observability: Optional[ObservabilityController] = None,
    ) -> None:
        self.planner = planner
        self.research_loop = research_loop
        self.llm = llm
        self.citation_manager = citation_manager
        self.entity_extractor = entity_extractor
        self.relation_builder = relation_builder
        self.relation_ranker = relation_ranker
        self.canonicalizer = canonicalizer
        self.graph_index = graph_index
        self.graph_persistence = graph_persistence
        self.graph_traverser = graph_traverser
        self.memory = memory_controller
        self.reasoning = ReasoningMemory()
        self.evaluator = EvaluationController(llm)
        self.improver = ImprovementEngine()
        self.hallucination_guard = HallucinationGuard()
        self.summarizer = ResearchSummarizer(llm=self.llm, guard=self.hallucination_guard)
        self.feedback_controller = FeedbackController(
            vector_service=getattr(self.research_loop, "vector_service", None),
            research_loop=self.research_loop,
            hallucination_guard=self.hallucination_guard,
        )
        self.observability = observability

    async def run(self, query: str):
        start_time = time.time()
        self.citation_manager.reset()
        past_memories = self.memory.recall(query)

        self.reasoning.start_group("research_session")
        self.reasoning.log(ReasoningEventType.PLANNING, "Research started", meta={"query": query, "past_memories": len(past_memories)})

        raw_evidence: List[Any] = await self.research_loop.run(query)
        self.reasoning.log(ReasoningEventType.EVIDENCE_FUSION, "Evidence retrieved", meta={"chunks": len(raw_evidence)})

        for result in raw_evidence:
            chunk = getattr(result, "chunk", result)
            entities = await self.entity_extractor.extract([chunk])
            normalized_entities = [self.canonicalizer.normalize_entity(entity) for entity in entities]
            self.graph_index.add_entities(normalized_entities)
            for entity in normalized_entities:
                self.graph_persistence.save_node(entity)

            relations = await self.relation_builder.build_relations(chunk, normalized_entities)
            ranked_relations = self.relation_ranker.rank(relations)
            for relation in ranked_relations:
                self.graph_index.add_relation(relation.src, relation.dst, relation.relation, relation.confidence, relation.evidence_chunk)
                self.graph_persistence.save_edge(relation)

        hidden_edges = await self.graph_traverser.find_connections(start_entity=query, max_hops=2)
        self.reasoning.log(ReasoningEventType.GRAPH_REASONING, "Graph traversal completed", meta={"edges_found": len(hidden_edges)})

        plan_obj = await self.planner.create_plan(query, raw_evidence, hidden_edges)
        sections = getattr(plan_obj, "sections", plan_obj)
        report = await self._compose_report(query, sections, raw_evidence, hidden_edges)
        citations = self.citation_manager.build_reference_list()
        if not citations:
            for item in raw_evidence:
                self.citation_manager.register_source(getattr(item, "chunk", item))
            citations = self.citation_manager.build_reference_list()
        self.reasoning.log(ReasoningEventType.SUMMARIZATION, "Answer generated", meta={"citations": len(citations)})

        self.memory.record(query=query, answer_summary=report[:500], tags=[], timestamp=time.time())

        research_answer = ResearchAnswer(
            query=query,
            answer=report,
            citations=citations,
            reasoning_steps=self.reasoning.summary(),
            evidences=[self._to_evidence_item(item) for item in raw_evidence],
        )
        evaluation = self.evaluator.evaluate(research_answer)
        suggestions = self.improver.suggest(evaluation)

        if self.observability:
            tracker = getattr(self.observability, "track_research_session", None)
            if callable(tracker):
                tracker(query=query, duration=time.time() - start_time, evidence_count=len(raw_evidence))

        self.reasoning.end_group("research_session")
        return {
            "report": report,
            "citations": citations,
            "evaluation": evaluation,
            "suggestions": suggestions,
            "reasoning": self.reasoning.summary(),
        }

    async def _compose_report(self, query: str, plan, raw_evidence: List[Any], hidden_edges: List[Any]) -> str:
        if hasattr(self.summarizer, "summarize"):
            try:
                return await self.summarizer.summarize(
                    query=query,
                    plan=plan,
                    raw_evidence=raw_evidence,
                    hidden_edges=hidden_edges,
                    citation_manager=self.citation_manager,
                )
            except TypeError:
                return await self.summarizer.summarize(query=query, evidence_chunks=[getattr(item, 'chunk', item) for item in raw_evidence])
        raise RuntimeError("Research summarizer is not configured correctly")

    def _to_evidence_item(self, item: Any) -> Evidence:
        chunk = getattr(item, "chunk", item)
        return Evidence(
            id=str(getattr(chunk, "chunk_id", getattr(item, "id", "unknown"))),
            text=str(getattr(chunk, "text", "")),
            source=str(getattr(chunk, "source", (getattr(chunk, "metadata", {}) or {}).get("source", "unknown"))),
        )
