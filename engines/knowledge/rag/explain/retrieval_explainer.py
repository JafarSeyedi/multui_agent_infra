class RetrievalExplainer:

    def __init__(self, llm):
        self.llm = llm

    async def explain(self, query, results):

        explanations = []

        for r in results[:5]:

            prompt = f"""
Explain briefly why this document chunk is relevant.

Query:
{query}

Chunk:
{r.chunk.text[:500]}

Answer in one sentence.
"""

            reason = await self.llm.text(prompt)

            explanations.append(
                {
                    "doc_id": r.chunk.id,
                    "score": r.score,
                    "reason": reason,
                }
            )

        return explanations
