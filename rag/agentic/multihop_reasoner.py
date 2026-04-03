class MultiHopReasoner:

    def __init__(self, llm):
        self.llm = llm

    async def generate_followup(self, query: str, evidence_text: str) -> str:
        prompt = f"""
We need more information to answer the question.
Generate a follow-up query that retrieves missing information.

Original query: {query}

Current evidence:
{evidence_text}

Return ONE follow-up query.
"""
        return await self.llm.text(prompt)
