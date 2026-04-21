from __future__ import annotations


class FeedbackController:
    def __init__(self, vector_service, research_loop, hallucination_guard=None):
        self.vector_service = vector_service
        self.research_loop = research_loop
        self.hallucination_guard = hallucination_guard

    async def apply_feedback(self, query, evidences, evaluation, positive_chunks, negative_chunks):
        if evaluation.hallucination_rate > 0.2 and self.hallucination_guard:
            self.hallucination_guard.enable_strict_mode()

        if evaluation.completeness_score < 0.6:
            self.research_loop.max_rounds += 1

        if self.vector_service is None:
            return

        if evaluation.retrieval_quality < 0.6:
            chosen_chunk_id = evidences[0].id if evidences else ""
            try:
                await self.vector_service.register_feedback(
                    query=query,
                    evidences=evidences,
                    results=[],
                    chosen_chunk_id=chosen_chunk_id,
                    positive_chunks=positive_chunks, 
                    negative_chunks=negative_chunks
                )
            except Exception:
                pass
