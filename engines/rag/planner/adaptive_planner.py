from .retrieval_plan import RetrievalPlan


class AdaptiveRetrievalPlanner:

    def __init__(
        self,
        llm=None,
        long_query_threshold: int = 12,
    ):
        self.llm = llm
        self.long_query_threshold = long_query_threshold

    async def plan(self, query: str) -> RetrievalPlan:

        words = query.split()
        n = len(words)

        # ---------------------------
        # Simple queries
        # ---------------------------

        if n <= 3:
            return RetrievalPlan(
                num_queries=1,
                top_k=5,
                use_rerank=False,
                compression="none"
            )

        # ---------------------------
        # Medium queries
        # ---------------------------

        if n <= self.long_query_threshold:
            return RetrievalPlan(
                num_queries=3,
                top_k=10,
                use_rerank=True,
                compression="embedding"
            )

        # ---------------------------
        # Complex queries
        # ---------------------------

        return RetrievalPlan(
            num_queries=5,
            top_k=20,
            use_rerank=True,
            compression="llm"
        )
