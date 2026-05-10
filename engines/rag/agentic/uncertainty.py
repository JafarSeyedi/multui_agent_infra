class UncertaintyEstimator:

    def __init__(self, llm):
        self.llm = llm

    async def score(self, query: str, evidence: list) -> float:
        text = "\n".join(e.chunk.text for e in evidence[:5])

        prompt = f"""
Given the original query and retrieved evidence,
estimate confidence on a scale 0–1
(0 = no useful evidence, 1 = fully supported).

Query: {query}

Evidence:
{text}

Return number only.
"""

        val = float(await self.llm.text(prompt))
        return min(max(val, 0), 1)
