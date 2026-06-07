class RetrievalAgentV2:

    def __init__(
        self,
        llm,
        decomposer,
        tracker,
        uncertainty_estimator,
        multihop_reasoner,
        max_rounds=4,
    ):
        self.llm = llm
        self.decomposer = decomposer
        self.tracker = tracker
        self.uncertainty = uncertainty_estimator
        self.multihop = multihop_reasoner
        self.max_rounds = max_rounds

    async def run(self, query, vector_service, top_k, filters):

        sub_queries = await self.decomposer.decompose(query)

        current_round = 0

        for sq in sub_queries:
            results = await vector_service.raw_retrieve(sq, top_k, filters)

            for r in results:
                r.source = "agentic"
                r.score *= vector_service.weight_manager.get("agentic")

            self.tracker.add(sq, results)

        # If everything has evidence → stop
        if not self.tracker.needs_more():
            return self.tracker.evidence[:top_k]

        # Otherwise begin multi-hop rounds
        while current_round < self.max_rounds:

            current_round += 1

            # Estimate uncertainty based on current evidence
            unc = await self.uncertainty.score(query, self.tracker.evidence)

            # If confident → stop
            if unc > 0.75:
                break

            # Multi-hop query next
            text = "\n".join([e.chunk.text for e in self.tracker.evidence[:5]])
            new_query = await self.multihop.generate_followup(query, text)

            results = await vector_service.raw_retrieve(
                new_query, top_k, filters
            )

            for r in results:
                r.source = "agentic"
                r.score *= vector_service.weight_manager.get("agentic")

            self.tracker.evidence.extend(results)

        return self.tracker.evidence[:top_k]
