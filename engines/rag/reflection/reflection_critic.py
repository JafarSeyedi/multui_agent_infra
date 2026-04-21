class RetrievalCritic:

    def __init__(self, llm):
        self.llm = llm

    async def evaluate(self, query: str, context_text: str) -> bool:
        """
        returns True if context is insufficient
        """
        prompt = f"""
You are a retrieval quality critic.

User Query:
{query}

Retrieved Context:
{context_text}

Evaluate if the context is sufficient to answer the query.
Answer only with: "sufficient" or "insufficient".
"""

        resp = await self.llm.generate(prompt)
        ans = resp.strip().lower()

        return "insufficient" in ans
