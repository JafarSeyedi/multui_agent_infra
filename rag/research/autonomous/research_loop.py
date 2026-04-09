from __future__ import annotations

from rag.research.memory.reasoning.event_types import ReasoningEventType
from rag.research.memory.reasoning_memory import ReasoningMemory


class AutonomousResearchLoop:
    def __init__(
        self,
        vector_service,
        gap_detector,
        query_generator,
        coverage_scorer,
        max_rounds: int = 4,
    ):
        self.vector_service = vector_service
        self.gap_detector = gap_detector
        self.query_generator = query_generator
        self.coverage_scorer = coverage_scorer
        self.max_rounds = max_rounds
        self.reasoning = ReasoningMemory()

    async def run(self, query):
        deduped = {}
        initial_results = await self.vector_service.query(query, top_k=15)
        for item in initial_results:
            deduped[getattr(item.chunk, 'chunk_id', str(id(item)))] = item

        for round_index in range(self.max_rounds):
            current_evidence = list(deduped.values())
            self.reasoning.start_group(f"research_round_{round_index + 1}")
            gaps = await self.gap_detector.detect_gaps(query, current_evidence)
            if not gaps:
                self.reasoning.end_group()
                break

            new_queries = await self.query_generator.generate(gaps)
            self.reasoning.log(
                ReasoningEventType.QUERY_EXPANSION,
                "Generated follow-up queries",
                meta={"count": len(new_queries), "round": round_index + 1},
            )

            for follow_up_query in new_queries:
                results = await self.vector_service.query(follow_up_query, top_k=10)
                for item in results:
                    deduped[getattr(item.chunk, 'chunk_id', str(id(item)))] = item

            coverage = await self.coverage_scorer.score(query, list(deduped.values()))
            self.reasoning.end_group()
            if coverage >= 0.85:
                break

        return list(deduped.values())
