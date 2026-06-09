from typing import Any


class RetrievalAgent:

    def __init__(self, planner, max_steps=3):
        self.planner = planner
        self.max_steps = max_steps

    async def answer(self, query: str, max_hops: int = 3, **options) -> dict[str, Any]:
        results = await self.run(query=query, vector_service=None, top_k=options.get("top_k", 10), filters=None)
        return {"query": query, "answer": "", "evidence": results}

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

            # ✅ Using raw retrieval
            results = await vector_service.raw_retrieve(
                query=current_query,
                top_k=top_k,
                filters=filters
            )

            # ✅ Convert to agentic evidence
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
