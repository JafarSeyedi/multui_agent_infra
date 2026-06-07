class QueryDecomposer:

    def __init__(self, llm):
        self.llm = llm

    async def decompose(self, query: str) -> list[str]:
        prompt = f"""
Break the following question into 2–4 independent, concise sub-questions
that help retrieve evidence. Use short sentences.

Query: {query}

Return JSON: ["...", "..."]
"""
        sub = await self.llm.json(prompt)
        return sub
