class RetrievalAgent:

    def __init__(self, planner, max_steps=3):
        self.planner = planner
        self.max_steps = max_steps

    async def run(
        self,
        query,
        vector_service,
        top_k,
        filters
    ):

        evidence = []
        current_query = query

        for _ in range(self.max_steps):

            # ✅ استفاده از raw retrieval
            results = await vector_service.raw_retrieve(
                query=current_query,
                top_k=top_k,
                filters=filters
            )

            # ✅ تبدیل به agentic evidence
            for r in results:

                r.source = "agentic"

                r.score = (
                    r.score *
                    vector_service.weight_manager.get("agentic")
                )

            evidence.extend(results)

            decision = await self.planner.next_action(
                query=query,
                evidence=evidence
            )

            if decision["action"] == "stop":
                break

            current_query = decision["next_query"]

        return evidence[:top_k]
